//===- WebAssemblyStackTagging.cpp - Manage linear stack allocations ------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
#include "WebAssemblyStackTagging.h"
#include "Utils/WasmAddressSpaces.h"
#include "llvm/IR/Module.h"
#include "llvm/Analysis/OptimizationRemarkEmitter.h"
#include "llvm/IR/DiagnosticInfo.h"
#include "llvm/IR/Dominators.h"
#include "llvm/IR/EHPersonalities.h"
#include "llvm/Transforms/Utils/Cloning.h"
#include "llvm/IR/CFG.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/InstIterator.h"
#include "llvm/IR/IntrinsicInst.h"
#include "llvm/IR/IntrinsicsWebAssembly.h"
#include "llvm/InitializePasses.h"
#include "llvm/Pass.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Target/TargetMachine.h"
#include "llvm/Transforms/Utils/Local.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/Transforms/Utils/MemoryTaggingSupport.h"
#include "llvm/Transforms/Utils/PromoteMemToReg.h"
#include <limits>

using namespace llvm;

#define DEBUG_TYPE "wasm-stack-tagging"

// The native Wasm EH target option is defined by WebAssemblyTargetMachine.
namespace llvm::WebAssembly {
extern cl::opt<bool> WasmEnableEH;
}

namespace {

static cl::opt<bool> FuseZeroInitialization(
    "wasm-memtag-fuse-zero-init", cl::Hidden, cl::init(true),
    cl::desc("Combine complete adjacent zero initialization with stack tagging"));

struct WebAssemblyStackTagging : public FunctionPass {
  static char ID;
  WebAssemblyStackTagging() : FunctionPass(ID) {}

  bool runOnFunction(Function &) override;

private:
  void getAnalysisUsage(AnalysisUsage &AU) const override {
    AU.addRequired<OptimizationRemarkEmitterWrapperPass>();
  }
};

inline bool canCombineStore(const memtag::AllocaInfo &Info, AllocaInst *AI,
                            DominatorTree *DT) {
  // Must have exactly one lifetime interval.
  if (Info.LifetimeStart.size() != 1 || Info.LifetimeEnd.size() != 1)
    return false;

  IntrinsicInst *Start = Info.LifetimeStart.front();

  // Check dominance and instruction order for every use.
  for (User *U : AI->users()) {
    auto *I = dyn_cast<Instruction>(U);
    if (!I)
      continue;

    // Lifetime intrinsics are not rewritten and do not matter.
    if (isa<LifetimeIntrinsic>(I))
      continue;

    // If Start does not dominate the use, combined tagging is unsafe.
    if (!DT->dominates(Start, I))
      return false;

    // If in the same block, Start must come before the use.
    if (Start->getParent() == I->getParent() && !Start->comesBefore(I))
      return false;
  }

  return true;
}

static const inline Align kTagGranuleSize = Align(16);

} // namespace

// Preserve the generation at which an address is passed, stored, converted,
// or derived while live. The SSA value for an earlier such use is never
// recovered from the current allocation tag. For pure address arithmetic
// hoisted to a definitely dead region, materialize the arithmetic at its first
// non-preparatory use. A loop-invariant address or integer representation
// must observe the active generation when passed to the guest ABI.
static void manageOwnerLifetimes(memtag::AllocaInfo &Info, DominatorTree &DT,
                         Type *IntPtrTy, uint64_t Size, ArrayRef<Instruction *> Exits) {
  AllocaInst *AI = Info.AI;
  Function *F = AI->getFunction();
  Module *M = F->getParent();
  SmallVector<AllocaInst *, 2> Registers;
  IRBuilder<> Entry(&*F->getEntryBlock().getFirstInsertionPt());
  Type *Ptr = AI->getType();
  // A changing token may cross multiple exceptional edges of one funclet.
  // Keep it in a private Wasm local on that path; EH preparation would
  // otherwise spill SSA PHIs into addressable linear memory.
  bool FuncletLocals = F->hasPersonalityFn() && WebAssembly::WasmEnableEH;
  unsigned RegisterSpace = FuncletLocals ? WebAssembly::WASM_ADDRESS_SPACE_VAR
                                         : F->getDataLayout().getAllocaAddrSpace();
  Type *StateTy = FuncletLocals ? Entry.getInt32Ty() : Entry.getInt1Ty();
  auto *Current = Entry.CreateAlloca(Ptr, RegisterSpace, nullptr, "memtag.current");
  Registers.push_back(Current);

  enum { Dead = 1, Live = 2 };
  DenseMap<BasicBlock *, unsigned> Incoming;
  DenseMap<BasicBlock *, SmallVector<IntrinsicInst *, 2>> Events;
  for (auto *I : Info.LifetimeStart)
    Events[I->getParent()].push_back(I);
  for (auto *I : Info.LifetimeEnd)
    Events[I->getParent()].push_back(I);
  for (auto &[BB, Markers] : Events)
    llvm::sort(Markers, [](auto *A, auto *B) { return A->comesBefore(B); });
  auto After = [](IntrinsicInst *I) -> unsigned {
    return I->getIntrinsicID() == Intrinsic::lifetime_start ? Live : Dead;
  };
  SmallVector<BasicBlock *, 8> Work{&F->getEntryBlock()};
  // Without any lifetime.start the alloca is initially live. A later
  // lifetime.end must still retire its issued pointer.
  bool StartsLive = Info.LifetimeStart.empty();
  Incoming[Work.back()] = StartsLive ? Live : Dead;
  while (!Work.empty()) {
    auto *BB = Work.pop_back_val();
    auto E = Events.find(BB);
    unsigned Out = E == Events.end() ? Incoming.lookup(BB) : After(E->second.back());
    for (auto *Succ : successors(BB)) {
      unsigned &In = Incoming[Succ];
      if (Out & ~In) {
        In |= Out;
        Work.push_back(Succ);
      }
    }
  }
  auto StateBefore = [&](Instruction *Pos) {
    BasicBlock *BB = Pos->getParent();
    unsigned State = Incoming.lookup(BB);
    if (auto E = Events.find(BB); E != Events.end())
      for (auto *Mark : E->second) {
        if (!Mark->comesBefore(Pos))
          break;
        State = After(Mark);
      }
    return State;
  };

  // A PHI receives its incoming pointer on its incoming edge. Snapshot the
  // original uses before creating any stores, loads, or cloned GEPs.
  struct Binding {
    Use *Operand;
    Instruction *At;
    Value *Address;
  };
  SmallVector<Binding, 8> Bindings;
  SmallVector<Value *, 8> Prepare{AI};
  while (!Prepare.empty()) {
    Value *Address = Prepare.pop_back_val();
    for (Use &U : Address->uses()) {
      auto *I = cast<Instruction>(U.getUser());
      if (isa<LifetimeIntrinsic>(I))
        continue;
      auto *Phi = dyn_cast<PHINode>(I);
      Instruction *At = Phi ? Phi->getIncomingBlock(U)->getTerminator() : I;
      unsigned State = StateBefore(At);
      if (!(State & Live) && U.getOperandNo() == 0 &&
          (isa<GetElementPtrInst, BitCastInst, PtrToIntInst, IntToPtrInst,
               ZExtInst, SExtInst, TruncInst>(I))) {
        Prepare.push_back(I);
        continue;
      }
      Bindings.push_back({&U, At, Address});
    }
  }

  // Reserve before any possible publication. The token is the tagged pointer,
  // validated together with the exact extent by the VM. Its effective backing
  // tag comes from release. The current VM only admits zero backing tags.
  Value *Length = ConstantInt::get(IntPtrTy, Size);
  auto Op = [&](Intrinsic::ID ID, IRBuilder<> &B, Value *Address) {
    auto *Fn = Intrinsic::getOrInsertDeclaration(M, ID, {IntPtrTy});
    return B.CreateCall(Fn, {B.getInt32(0), Address, Length});
  };
  auto *Active = Entry.CreateAlloca(StateTy, RegisterSpace, nullptr, "memtag.active");
  Registers.push_back(Active);
  IRBuilder<> Init(AI->getNextNode());
  Init.CreateStore(Op(StartsLive ? Intrinsic::wasm_memtag_claim
                                : Intrinsic::wasm_memtag_reserve,
                      Init, AI), Current);
  Init.CreateStore(ConstantInt::get(StateTy, StartsLive), Active);
  DenseMap<Instruction *, unsigned> States;
  for (auto *I : Info.LifetimeStart)
    States[I] = StateBefore(I);
  for (auto *I : Info.LifetimeEnd)
    States[I] = StateBefore(I);
  for (auto *Start : Info.LifetimeStart) {
    IRBuilder<> B(Start);
    auto *Token = B.CreateLoad(Ptr, Current);
    auto Restart = [&](IRBuilder<> &LivePath) {
      auto *Parent = Op(Intrinsic::wasm_memtag_release, LivePath, Token);
      LivePath.CreateStore(Op(Intrinsic::wasm_memtag_claim, LivePath, Parent),
                           Current);
    };
    auto Activate = [&](IRBuilder<> &DeadPath) {
      DeadPath.CreateStore(Op(Intrinsic::wasm_memtag_activate, DeadPath, Token),
                           Current);
    };
    unsigned State = States.lookup(Start);
    if (State == Live) {
      Restart(B);
    } else if (State == (Live | Dead)) {
      Instruction *IfLive, *IfDead;
      SplitBlockAndInsertIfThenElse(B.CreateIsNotNull(B.CreateLoad(StateTy, Active)),
                                    Start, &IfLive, &IfDead);
      IRBuilder<> LB(IfLive), DB(IfDead);
      Restart(LB);
      Activate(DB);
    } else {
      Activate(B);
    }
    IRBuilder<> Update(Start);
    Update.CreateStore(ConstantInt::get(StateTy, 1), Active);
  }
  for (auto *End : Info.LifetimeEnd) {
    unsigned State = States.lookup(End);
    if (!(State & Live))
      continue;
    IRBuilder<> B(End);
    if (State & Dead) {
      auto *IfLive = SplitBlockAndInsertIfThen(
          B.CreateIsNotNull(B.CreateLoad(StateTy, Active)), End, false);
      B.SetInsertPoint(IfLive);
    }
    auto *Token = B.CreateLoad(Ptr, Current);
    auto *Parent = Op(Intrinsic::wasm_memtag_release, B, Token);
    B.CreateStore(Op(Intrinsic::wasm_memtag_reserve, B, Parent), Current);
    B.CreateStore(ConstantInt::get(StateTy, 0), Active);
  }
  // General-case objects always hold exactly one pending or active token.
  // Retire both states before every supported frame exit.
  for (auto *Exit : Exits) {
    IRBuilder<> B(Exit);
    Op(Intrinsic::wasm_memtag_release, B, B.CreateLoad(Ptr, Current));
  }

  // A switch may send several edges to the same successor. LLVM requires
  // identical incoming values for a PHI on repeated edges from one block.
  // Each such edge observes exactly the same token at its terminator.
  DenseMap<std::pair<Instruction *, Value *>, Value *> Materialized;
  for (auto &[Operand, At, Address] : Bindings) {
    auto Key = std::make_pair(At, Address);
    if (Value *Previous = Materialized.lookup(Key)) {
      Operand->set(Previous);
      continue;
    }
    IRBuilder<> B(At);
    Value *PtrValue = B.CreateLoad(Ptr, Current);
    SmallVector<Instruction *, 4> Derivation;
    for (Value *Step = Address; Step != AI;) {
      auto *I = cast<Instruction>(Step);
      Derivation.push_back(I);
      Step = I->getOperand(0);
    }
    for (Instruction *I : llvm::reverse(Derivation)) {
      Instruction *Copy = I->clone();
      Copy->setOperand(0, PtrValue);
      B.Insert(Copy);
      PtrValue = Copy;
    }
    Materialized[Key] = PtrValue;
    Operand->set(PtrValue);
  }
  // These are compiler registers. They must never be addressable Wasm slots.
  DT.recalculate(*F);
  if (!FuncletLocals)
    PromoteMemToReg(Registers, DT);
  // Backend stack colouring cannot overlay an outstanding reservation with
  // another physical object. Owner operations carry the complete lifetime.
  for (auto *I : Info.LifetimeStart)
    I->eraseFromParent();
  for (auto *I : Info.LifetimeEnd)
    I->eraseFromParent();
}

static void reportOwnerError(Instruction &I, const Twine &Message) {
  const Function &F = *I.getFunction();
  DiagnosticLocation Loc = I.getDebugLoc()
                               ? DiagnosticLocation(I.getDebugLoc())
                               : DiagnosticLocation(F.getSubprogram());
  F.getContext().diagnose(DiagnosticInfoUnsupported(F, Message, Loc));
}

// Make native Wasm frame escapes explicit before owner-token SSA is built.
// The outer cleanuppad catches all exception tags and rethrows the original
// exception after the frame's current owner tokens have been released. Existing
// typed handlers and local cleanup-to-handler edges keep their destinations.
static bool prepareOwnerUnwind(Function &F, memtag::StackInfo &Info) {
  SmallVector<CallInst *, 8> Calls;
  SmallVector<CatchSwitchInst *, 4> Switches;
  SmallVector<CleanupReturnInst *, 4> CleanupReturns;
  DenseMap<Instruction *, Value *> UnwindMemo;
  auto constrainedDestination = [&](Instruction *Pad) -> BasicBlock * {
    auto *Dest = dyn_cast_or_null<Instruction>(getScopedUnwindDestToken(Pad, UnwindMemo));
    return Dest ? Dest->getParent() : nullptr;
  };
  auto reject = [&](Instruction &I) {
    reportOwnerError(I, "strict WasmMTE cannot match this non-local "
                                 "exit to an exact stack-owner release");
    return false;
  };
  for (Instruction &I : instructions(F)) {
    if (auto *Call = dyn_cast<CallInst>(&I)) {
      if (Call->canReturnTwice())
        return reject(I);
      if (F.doesNotThrow() || Call->doesNotThrow() || Call->isMustTailCall())
        continue;
      if (!WebAssembly::WasmEnableEH || Call->isInlineAsm() ||
          Call->getIntrinsicID() == Intrinsic::experimental_deoptimize ||
          Call->getIntrinsicID() == Intrinsic::experimental_guard)
        return reject(I);
      if (auto Funclet = Call->getOperandBundle(LLVMContext::OB_funclet))
        if (constrainedDestination(cast<Instruction>(Funclet->Inputs[0])))
          return reject(I);
      Calls.push_back(Call);
    } else if (auto *CS = dyn_cast<CatchSwitchInst>(&I)) {
      if (CS->unwindsToCaller()) {
        if (!WebAssembly::WasmEnableEH)
          return reject(I);
        if (auto *Parent = dyn_cast<Instruction>(CS->getParentPad()))
          if (constrainedDestination(Parent))
            return reject(I);
        Switches.push_back(CS);
      }
    } else if (auto *CR = dyn_cast<CleanupReturnInst>(&I)) {
      if (CR->unwindsToCaller())
        CleanupReturns.push_back(CR);
    }
  }
  if (Calls.empty() && Switches.empty())
    return true;
  if (F.hasPersonalityFn() &&
      classifyEHPersonality(F.getPersonalityFn()) != EHPersonality::Wasm_CXX)
    return reject(F.getEntryBlock().front());
  if (!F.hasPersonalityFn()) {
    auto *FT = FunctionType::get(Type::getInt32Ty(F.getContext()), true);
    auto Person = F.getParent()->getOrInsertFunction(
        getEHPersonalityName(EHPersonality::Wasm_CXX), FT);
    F.setPersonalityFn(cast<Constant>(Person.getCallee()));
  }
  // Ensure entry allocas (and their generated tokens) dominate even the first
  // throwing call. Static Wasm stack slots have control-independent sizes.
  auto At = F.getEntryBlock().getFirstInsertionPt();
  for (auto &[AI, Allocation] : Info.AllocasToInstrument)
    if (AI->getIterator() != At)
      AI->moveBeforePreserving(F.getEntryBlock(), At);
  auto *Outer = BasicBlock::Create(F.getContext(), "memtag.unwind", &F);
  IRBuilder<> B(Outer);
  auto *Pad = B.CreateCleanupPad(ConstantTokenNone::get(F.getContext()), {});
  B.CreateCleanupRet(Pad, nullptr);
  for (auto *C : Calls)
    changeToInvokeAndSplitBasicBlock(C, Outer);
  for (auto *CS : Switches) {
    auto *Redirect = CatchSwitchInst::Create(CS->getParentPad(), Outer,
                                  CS->getNumHandlers(), "", CS->getIterator());
    Redirect->setDebugLoc(CS->getDebugLoc());
    for (BasicBlock *Handler : CS->handlers())
      Redirect->addHandler(Handler);
    Redirect->takeName(CS);
    CS->replaceAllUsesWith(Redirect);
    CS->eraseFromParent();
  }
  for (auto *CR : CleanupReturns) {
    auto *Redirect = CleanupReturnInst::Create(CR->getCleanupPad(), Outer,
                                                CR->getIterator());
    Redirect->setDebugLoc(CR->getDebugLoc());
    CR->eraseFromParent();
  }
  Info.RetVec.clear();
  for (Instruction &I : instructions(F)) {
    if (auto *CR = dyn_cast<CleanupReturnInst>(&I); CR && !CR->unwindsToCaller())
      continue;
    if (auto *Exit = memtag::getUntagLocationIfFunctionExit(I))
      Info.RetVec.push_back(Exit);
  }
  return true;
}

bool WebAssemblyStackTagging::runOnFunction(Function &Fn) {
  if (!Fn.hasFnAttribute(Attribute::SanitizeMemTag))
    return false;

  Triple triplet(Fn.getParent()->getTargetTriple());
  bool iswasm32 = triplet.getArch() == ::llvm::Triple::wasm32;

  Function *F = &Fn;
  const DataLayout *DL = &Fn.getParent()->getDataLayout();
  SmallVector<AllocaInst *, 8> Registers;
  for (Instruction &I : instructions(Fn)) {
    if (auto *II = dyn_cast<IntrinsicInst>(&I);
        II && II->getIntrinsicID() == Intrinsic::structured_alloca) {
      reportOwnerError(I,
          "strict WasmMTE stack ownership cannot claim structured allocation");
      return false;
    }
    auto *AI = dyn_cast<AllocaInst>(&I);
    if (!AI || AI->isSwiftError())
      continue;
    auto Bytes = AI->getAllocationSize(*DL);
    if (!AI->isStaticAlloca() || AI->isUsedWithInAlloca() ||
        !Bytes || Bytes->isScalable()) {
      reportOwnerError(I,
          "strict WasmMTE stack ownership requires a statically bounded "
          "allocation with an exact release");
      return false;
    }
    uint64_t Max = iswasm32 ? std::numeric_limits<uint32_t>::max()
                            : std::numeric_limits<uint64_t>::max();
    if (Bytes->getFixedValue() > Max - (kTagGranuleSize.value() - 1)) {
      reportOwnerError(I,
          "strict WasmMTE padded extent does not fit the memory address width");
      return false;
    }
    if (isAllocaPromotable(AI))
      Registers.push_back(AI);
  }
  // A promotable value needs no owner only after it has actually left
  // linear memory. A bounded use of a surviving physical slot cannot
  // prove safety against an access through another object.
  if (!Registers.empty()) {
    DominatorTree PromoteDT(Fn);
    // Promoting a local pointer may expose another promotable allocation.
    // Remove it as well before StackInfoBuilder classifies physical storage.
    do {
      PromoteMemToReg(Registers, PromoteDT);
      Registers.clear();
      for (Instruction &I : Fn.getEntryBlock())
        if (auto *AI = dyn_cast<AllocaInst>(&I);
            AI && !AI->isSwiftError() && isAllocaPromotable(AI))
          Registers.push_back(AI);
    } while (!Registers.empty());
  }

  OptimizationRemarkEmitter &ORE =
      getAnalysis<OptimizationRemarkEmitterWrapperPass>().getORE();

  memtag::StackInfoBuilder SIB(nullptr, "webassembly-stack-tagging");
  for (Instruction &I : instructions(F))
    SIB.visit(ORE, I);
  memtag::StackInfo &SInfo = SIB.get();
  // A cleanupret can transfer to another cleanup/catch in this same function.
  // Its frame and surviving objects are still live on that edge. Only a return
  // to the caller retires the entire frame; ordinary lifetime ends remain
  // responsible for individual objects during an internal cleanup.
  llvm::erase_if(SInfo.RetVec, [](Instruction *I) {
    const auto *Return = dyn_cast<CleanupReturnInst>(I);
    return Return && !Return->unwindsToCaller();
  });

  DominatorTree DT(Fn);
  auto &AllocasToInstrument = SInfo.AllocasToInstrument;
  if (AllocasToInstrument.empty()) {
    return true;
  }
  if (!prepareOwnerUnwind(Fn, SInfo))
    return false;
  DT.recalculate(Fn);

  LLVMContext &Ctx = Fn.getContext();
  Type *Int32Type = Type::getInt32Ty(Ctx);
  Type *IntPtrType = iswasm32 ? Int32Type : Type::getInt64Ty(Ctx);

  for (auto &I : AllocasToInstrument) {
    memtag::AllocaInfo &Info = I.second;
    memtag::alignAndPadAlloca(Info, kTagGranuleSize);
    AllocaInst *AI = Info.AI;
    IRBuilder<> IRB(Info.AI->getNextNode());

    auto Size = AI->getAllocationSize(*DL)->getFixedValue();
    auto *Length = ConstantInt::get(IntPtrType, Size);
    auto Op = [&](Intrinsic::ID ID, IRBuilder<> &B, Value *Address) {
      auto *Decl = Intrinsic::getOrInsertDeclaration(F->getParent(), ID,
                                                     {IntPtrType});
      return B.CreateCall(Decl, {B.getInt32(0), Address, Length});
    };
    if (Info.LifetimeStart.empty() && Info.LifetimeEnd.empty()) {
      auto *Tagged = Op(Intrinsic::wasm_memtag_claim, IRB, AI);
      AI->replaceUsesWithIf(Tagged, [&](const Use &U) {
        return U.getUser() != Tagged && !isa<LifetimeIntrinsic>(U.getUser());
      });
      for (Instruction *Exit : SInfo.RetVec) {
        IRBuilder<> B(Exit);
        Op(Intrinsic::wasm_memtag_release, B, Tagged);
      }
      for (auto *End : Info.LifetimeEnd)
        End->eraseFromParent();
      continue;
    }
    // A straight-line interval keeps claim and release on exactly the same
    // dynamic path, including repeated executions of that block in a loop.
    if (canCombineStore(Info, AI, &DT) &&
        Info.LifetimeStart.front()->getParent() == Info.LifetimeEnd.front()->getParent() &&
        Info.LifetimeStart.front()->comesBefore(Info.LifetimeEnd.front())) {
      auto *Start = Info.LifetimeStart.front();
      auto *End = Info.LifetimeEnd.front();
      auto *Zero = FuseZeroInitialization
                       ? dyn_cast_or_null<MemSetInst>(Start->getNextNode()) : nullptr;
      auto *Bytes = Zero ? dyn_cast<ConstantInt>(Zero->getLength()) : nullptr;
      auto *Byte = Zero ? dyn_cast<ConstantInt>(Zero->getValue()) : nullptr;
      if (Zero && (Zero->isVolatile() || !Bytes || !Byte || !Byte->isZero() ||
                   Zero->getDest()->stripPointerCasts() != AI ||
                   Bytes->getValue() != Size))
        Zero = nullptr;
      IRBuilder<> B(Start);
      auto *Tagged = Op(Zero ? Intrinsic::wasm_memtag_claimz
                             : Intrinsic::wasm_memtag_claim, B, AI);
      AI->replaceUsesWithIf(Tagged, [&](const Use &U) {
        return U.getUser() != Tagged && !isa<LifetimeIntrinsic>(U.getUser());
      });
      IRBuilder<> Finish(End);
      Op(Intrinsic::wasm_memtag_release, Finish, Tagged);
      if (Zero)
        Zero->eraseFromParent();
      Start->eraseFromParent();
      End->eraseFromParent();
    } else {
      manageOwnerLifetimes(Info, DT, IntPtrType, Size, SInfo.RetVec);
    }
  }

  // StackInfoBuilder coalesces duplicate lifetime.end markers in a block.
  // No marker may remain for a frame slot while a reservation exists.
  for (auto &[Original, Info] : AllocasToInstrument) {
    SmallVector<LifetimeIntrinsic *, 2> Remaining;
    for (User *U : Info.AI->users())
      if (auto *Marker = dyn_cast<LifetimeIntrinsic>(U))
        Remaining.push_back(Marker);
    for (auto *Marker : Remaining)
      Marker->eraseFromParent();
  }
  return true;
}

char WebAssemblyStackTagging::ID = 0;
INITIALIZE_PASS_BEGIN(WebAssemblyStackTagging, DEBUG_TYPE,
                      "WebAssembly Stack Tagging", false, false)
INITIALIZE_PASS_DEPENDENCY(OptimizationRemarkEmitterWrapperPass)
INITIALIZE_PASS_END(WebAssemblyStackTagging, DEBUG_TYPE,
                    "WebAssembly Stack Tagging", false, false)

FunctionPass *llvm::createWebAssemblyStackTaggingPass() {
  return new WebAssemblyStackTagging();
}
