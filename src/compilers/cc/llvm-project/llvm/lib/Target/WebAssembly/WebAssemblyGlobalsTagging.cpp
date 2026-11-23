//===- WebAssemblyGlobalsTagging.cpp - Global tagging in IR ---------------===//
//
//                     The LLVM Compiler Infrastructure
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//
//===----------------------------------------------------------------------===//

#include "WebAssembly.h"
#include "llvm/ADT/DenseMap.h"
#include "llvm/ADT/DenseSet.h"
#include "llvm/IR/Attributes.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/GlobalAlias.h"
#include "llvm/IR/GlobalValue.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IntrinsicInst.h"
#include "llvm/IR/IntrinsicsWebAssembly.h"
#include "llvm/IR/Module.h"
#include "llvm/Pass.h"
#include "llvm/Support/raw_ostream.h"

#include <algorithm>
#include <utility>
#include <vector>

using namespace llvm;

static const Align kTagGranuleSize = Align(16);

static bool shouldTagGlobal(GlobalVariable &G) {
  if (!G.isTagged())
    return false;

  assert(G.hasSanitizerMetadata() &&
         "Missing sanitizer metadata, but symbol is apparently tagged.");
  GlobalValue::SanitizerMetadata Meta = G.getSanitizerMetadata();

  // A compiler-owned constant may be a pooled string, a type-identity token
  // or part of a linker table. Only source objects own padding and a tag.
  if (G.getName().starts_with("llvm.") ||
      (G.isConstant() && (!G.getMetadata("wasm.memtag.object") ||
                          G.hasSection()))) {
    Meta.Memtag = false;
    G.setSanitizerMetadata(Meta);
    return false;
  }

  return true;
}

// Technically, due to ELF symbol interposition semantics, we can't change the
// alignment or size of symbols. If we increase the alignment or size of a
// symbol, the compiler may make optimisations based on this new alignment or
// size. If the symbol is interposed, this optimisation could lead to
// alignment-related or OOB read/write crashes.
//
// This is handled in the linker. When the linker sees multiple declarations of
// a global variable, and some are tagged, and some are untagged, it resolves it
// to be an untagged definition - but preserves the tag-granule-rounded size and
// tag-granule-alignment. This should prevent these kind of crashes intra-DSO.
// For cross-DSO, it's been a reasonable contract that if you're interposing a
// sanitizer-instrumented global, then the interposer also needs to be
// sanitizer-instrumented.
//
// FIXME: In theory, this can be fixed by splitting the size/alignment of
// globals into two uses: an "output alignment" that's emitted to the ELF file,
// and an "optimisation alignment" that's used for optimisation. Thus, we could
// adjust the output alignment only, and still optimise based on the pessimistic
// pre-tagging size/alignment.
static GlobalVariable *tagGlobalDefinition(Module &M, GlobalVariable *G) {
  Constant *Initializer = G->getInitializer();
  uint64_t SizeInBytes =
      M.getDataLayout().getTypeAllocSize(Initializer->getType());

  uint64_t NewSize = alignTo(SizeInBytes, kTagGranuleSize);
  if (SizeInBytes != NewSize) {
    // Pad the initializer out to the next multiple of 16 bytes.
    llvm::SmallVector<uint8_t> Init(NewSize - SizeInBytes, 0);
    Constant *Padding = ConstantDataArray::get(M.getContext(), Init);
    Initializer = ConstantStruct::getAnon({Initializer, Padding});
    auto *NewGV = new GlobalVariable(
        M, Initializer->getType(), G->isConstant(), G->getLinkage(),
        Initializer, "", G, G->getThreadLocalMode(), G->getAddressSpace());
    NewGV->copyAttributesFrom(G);
    NewGV->setComdat(G->getComdat());
    NewGV->copyMetadata(G, 0);

    NewGV->takeName(G);
    G->replaceAllUsesWith(NewGV);
    G->eraseFromParent();
    G = NewGV;
  }

  G->setAlignment(std::max(G->getAlign().valueOrOne(), kTagGranuleSize));

  // Ensure that tagged globals don't get merged by ICF - as they should have
  // different tags at runtime.
  G->setUnnamedAddr(GlobalValue::UnnamedAddr::None);

  return G;
}

static bool
containsTaggedGlobal(const Constant *C,
                     const DenseSet<const GlobalValue *> &TaggedGlobals) {
  if (const auto *G = dyn_cast<GlobalValue>(C))
    return TaggedGlobals.contains(G);
  for (const Value *Op : C->operands())
    if (const auto *OpC = dyn_cast<Constant>(Op))
      if (containsTaggedGlobal(OpC, TaggedGlobals))
        return true;
  return false;
}

namespace {

/// Replaces every use of a tagged global inside a function with a pointer
/// whose tag was materialized by the runtime. This is the wasm equivalent of
/// AArch64 forcing tagged globals through the GOT: the tag is only known once
/// the module has been instantiated (see the "memtag.globals" descriptor
/// section emitted by the linker), so it cannot be folded into the address.
class TaggedGlobalUseMaterializer {
public:
  TaggedGlobalUseMaterializer(
      Function &F, const DenseSet<const GlobalValue *> &TaggedGlobals,
      Function *MemtagLoad)
      : F(F), TaggedGlobals(TaggedGlobals), MemtagLoad(MemtagLoad) {}

  void run() {
    // Materialization can split the entry block and create PHIs. Visit only
    // original instructions: rewriting a generated fallback pointer would
    // otherwise turn the new PHI into its own incoming value.
    SmallVector<Instruction *> Worklist;
    for (BasicBlock &BB : F)
      for (Instruction &I : BB)
        Worklist.push_back(&I);
    for (Instruction *I : Worklist)
      rewriteOperands(*I);
  }

private:
  Value *getTaggedPtr(GlobalValue *G) {
    auto It = TaggedPtrs.find(G);
    if (It != TaggedPtrs.end())
      return It->second;

    BasicBlock &Entry = F.getEntryBlock();
    if (auto *Variable = dyn_cast<GlobalVariable>(G);
        Variable && !Variable->isDeclaration()) {
      IRBuilder<> Builder(&*Entry.getFirstInsertionPt());
      CallInst *TaggedPtr =
          Builder.CreateCall(MemtagLoad, {Builder.getInt32(0), G});
      TaggedPtrs.insert({G, TaggedPtr});
      return TaggedPtr;
    }

    // External data declarations also describe linker address constants such
    // as __heap_end. An address exactly at/past memory end is valid for address
    // arithmetic, but there is no allocation tag to read there. Preserve that
    // raw address; a later actual dereference still performs ordinary bounds
    // and tag checks. Do not weaken memtag.load or maintain a symbol blacklist.
    auto *IntPtrTy = F.getParent()->getDataLayout().getIntPtrType(F.getContext());
    // Preserve static entry allocas when adding the external-address guard.
    // Moving them into Continue makes isStaticAlloca() false, which would
    // silently remove their stack MTE instrumentation in the next pass.
    SmallVector<AllocaInst *, 8> EntryAllocas;
    for (Instruction &I : Entry)
      if (auto *AI = dyn_cast<AllocaInst>(&I); AI && AI->isStaticAlloca())
        EntryAllocas.push_back(AI);
    auto *Continue = Entry.splitBasicBlock(Entry.getFirstInsertionPt(),
                                          "memtag.global.cont");
    for (AllocaInst *AI : EntryAllocas)
      AI->moveBefore(Entry.getTerminator()->getIterator());
    Entry.getTerminator()->eraseFromParent();
    auto *Check = BasicBlock::Create(F.getContext(), "memtag.global.check", &F,
                                    Continue);
    auto *Load = BasicBlock::Create(F.getContext(), "memtag.global.load", &F,
                                   Continue);
    IRBuilder<> Builder(&Entry);
    // memory.size on a shared memory is an observable atomic load. Keeping it
    // outside this guard prevents a runtime that erases MTE from eliminating
    // the unused query. status folds to zero when instrumentation is disabled;
    // an enabled runtime still performs the complete bounds/null guard.
    Function *Status = Intrinsic::getOrInsertDeclaration(
        F.getParent(), Intrinsic::wasm_memtag_status, {IntPtrTy});
    Value *Enabled = Builder.CreateICmpNE(
        Builder.CreateCall(Status, {Builder.getInt32(0)}),
        ConstantInt::get(IntPtrTy, 0));
    Builder.CreateCondBr(Enabled, Check, Continue);
    Builder.SetInsertPoint(Check);
    Value *Address = Builder.CreatePtrToInt(G, IntPtrTy);
    Function *MemorySize = Intrinsic::getOrInsertDeclaration(
        F.getParent(), Intrinsic::wasm_memory_size, {IntPtrTy});
    Value *Pages = Builder.CreateCall(MemorySize, {Builder.getInt32(0)});
    // Compare page numbers instead of multiplying page count by 65536, which
    // would overflow at the full memory32/memory64 address-space boundary.
    Value *Inside = Builder.CreateICmpULT(
        Builder.CreateLShr(Address, 16), Pages);
    // An unresolved extern_weak data symbol has the null address. Loading
    // granule zero's allocation tag would turn it into a nonnull pointer if
    // that granule was retagged. Keep weak null tests independent of shadow
    // contents; a real null dereference still goes through runtime checking.
    if (G->hasExternalWeakLinkage())
      Inside = Builder.CreateAnd(
          Inside, Builder.CreateICmpNE(
                      G, ConstantPointerNull::get(cast<PointerType>(G->getType()))));
    Builder.CreateCondBr(Inside, Load, Continue);
    Builder.SetInsertPoint(Load);
    Value *TaggedPtr =
        Builder.CreateCall(MemtagLoad, {Builder.getInt32(0), G});
    Builder.CreateBr(Continue);
    auto *Result = PHINode::Create(G->getType(), 3, "memtag.global.pointer",
                                  Continue->begin());
    Result->addIncoming(G, &Entry);
    Result->addIncoming(G, Check);
    Result->addIncoming(TaggedPtr, Load);
    TaggedPtrs.insert({G, Result});
    return Result;
  }

  // SROA and SLP may turn several scalar field stores into one constant
  // vector or nested aggregate. Preserve the runtime pointer provenance of
  // every tagged leaf (including GEPs), while keeping untagged lanes constant.
  Value *materializeConstant(Constant *C, Instruction *Before) {
    if (auto *G = dyn_cast<GlobalValue>(C))
      return getTaggedPtr(G);

    if (auto *CE = dyn_cast<ConstantExpr>(C)) {
      Instruction *I = CE->getAsInstruction();
      I->insertBefore(Before->getIterator());
      for (Use &U : I->operands()) {
        auto *Part = dyn_cast<Constant>(U.get());
        if (Part && containsTaggedGlobal(Part, TaggedGlobals))
          U.set(materializeConstant(Part, I));
      }
      return I;
    }

    if (auto *Aggregate = dyn_cast<ConstantAggregate>(C)) {
      Value *Result = C;
      bool IsVector = C->getType()->isVectorTy();
      for (unsigned Index = 0; Index < Aggregate->getNumOperands(); ++Index) {
        Constant *Part = Aggregate->getOperand(Index);
        if (!containsTaggedGlobal(Part, TaggedGlobals))
          continue;
        Value *Tagged = materializeConstant(Part, Before);
        IRBuilder<> Builder(Before);
        if (IsVector)
          Result = Builder.CreateInsertElement(Result, Tagged, Index);
        else
          Result = Builder.CreateInsertValue(Result, Tagged, Index);
      }
      return Result;
    }
    return C;
  }

  void rewriteOperands(Instruction &I) {
    // EH pad clauses and typeid selectors encode constant type identities for
    // the backend/LSDA, not executed linear-memory accesses. Turning them into
    // tagged SSA pointers violates the LLVM IR contract. Loads through an RTTI
    // pointer in ordinary code are still materialized and checked normally.
    if (isa<CatchPadInst, CleanupPadInst, LandingPadInst>(I))
      return;
    if (auto *Intrinsic = dyn_cast<IntrinsicInst>(&I);
        Intrinsic && Intrinsic->getIntrinsicID() == Intrinsic::eh_typeid_for)
      return;
    // An explicit untag of a bare symbol asks only for its numerical address.
    // Looking up the allocation tag where an absolute linker value happens to
    // point is unnecessary. Leave all actual data references materialized.
    if (auto *II = dyn_cast<IntrinsicInst>(&I);
        II && II->getIntrinsicID() == Intrinsic::wasm_memtag_untag &&
        isa<GlobalVariable>(II->getArgOperand(1)))
      return;
    if (auto *CB = dyn_cast<CallBase>(&I);
        CB && CB->getCalledFunction() == MemtagLoad)
      return;
    if (auto *Intrinsic = dyn_cast<IntrinsicInst>(&I);
        Intrinsic && Intrinsic->getIntrinsicID() == Intrinsic::threadlocal_address) {
      // The intrinsic must retain its constant TLS symbol operand. Materialize
      // the allocation tag on the resolved per-thread address, not on the
      // link-time TLS offset or on a different thread's template address.
      auto *Global = dyn_cast<GlobalValue>(Intrinsic->getArgOperand(0));
      if (Global && TaggedGlobals.contains(Global)) {
        IRBuilder<> Builder(Intrinsic->getNextNode());
        auto *Tagged = Builder.CreateCall(
            MemtagLoad, {Builder.getInt32(0), Intrinsic});
        Intrinsic->replaceUsesWithIf(Tagged, [Tagged](Use &U) {
          return U.getUser() != Tagged;
        });
      }
      return;
    }

    // A switch can have multiple edges from the same predecessor to one
    // PHI. LLVM requires identical SSA values on those duplicate edges.
    // Key by the terminator so an entry split during materialization keeps
    // the same identity even if the instruction changes its parent block.
    DenseMap<std::pair<Instruction *, Constant *>, Value *> PhiConstants;
    for (Use &U : I.operands()) {
      Value *Op = U.get();
      if (auto *G = dyn_cast<GlobalValue>(Op);
          G && TaggedGlobals.contains(G)) {
        U.set(getTaggedPtr(G));
      } else if (auto *C = dyn_cast<Constant>(Op);
                 C && (isa<ConstantExpr, ConstantAggregate>(C)) &&
                 containsTaggedGlobal(C, TaggedGlobals)) {
        // A PHI operand is evaluated on its incoming edge. Inserting before
        // the PHI would both split the PHI group and fail to dominate that
        // edge. These pure constant expressions may safely be evaluated
        // before the predecessor terminator, including on a critical edge.
        if (auto *Phi = dyn_cast<PHINode>(&I)) {
          Instruction *Terminator =
              Phi->getIncomingBlock(U.getOperandNo())->getTerminator();
          auto Inserted = PhiConstants.try_emplace({Terminator, C}, nullptr);
          if (Inserted.second)
            Inserted.first->second = materializeConstant(C, Terminator);
          U.set(Inserted.first->second);
        } else {
          U.set(materializeConstant(C, &I));
        }
      }
    }
  }

  Function &F;
  const DenseSet<const GlobalValue *> &TaggedGlobals;
  Function *MemtagLoad;
  DenseMap<GlobalValue *, Value *> TaggedPtrs;
};

} // anonymous namespace

namespace {
class WebAssemblyGlobalsTagging : public ModulePass {
public:
  static char ID;

  explicit WebAssemblyGlobalsTagging() : ModulePass(ID) {
    initializeWebAssemblyGlobalsTaggingPass(*PassRegistry::getPassRegistry());
  }

  bool runOnModule(Module &M) override;

  StringRef getPassName() const override {
    return "WebAssembly Globals Tagging";
  }
};
} // anonymous namespace

char WebAssemblyGlobalsTagging::ID = 0;

bool WebAssemblyGlobalsTagging::runOnModule(Module &M) {
  // No mutating the globals in-place, or iterator invalidation occurs.
  std::vector<GlobalVariable *> GlobalsToTag;
  for (GlobalVariable &G : M.globals()) {
    if (G.isDeclaration() || !shouldTagGlobal(G))
      continue;

    // LLD materializes tags in data pointer relocations before user code, so
    // static pointer initializers no longer exclude their targets from MTE.
    GlobalsToTag.push_back(&G);
  }

  DenseSet<const GlobalValue *> TaggedGlobals;
  for (GlobalVariable *G : GlobalsToTag)
    TaggedGlobals.insert(tagGlobalDefinition(M, G));

  // An instrumented function can refer to a tagged definition in another
  // translation unit. Weak data aliases may also resolve to such a definition
  // at link time (musl __stdio_exit is one example). Materialize the resolved
  // symbol's tag rather than assuming that an external/aliased address is tag 0.
  // Untagged definitions naturally load tag 0. Function/table identities are
  // not linear-memory pointers and must never enter this path.
  DenseSet<const GlobalValue *> InstrumentedGlobals(TaggedGlobals);
  for (GlobalVariable &G : M.globals())
    if (G.isDeclaration() &&
        !G.getName().starts_with("llvm."))
      InstrumentedGlobals.insert(&G);
  for (GlobalAlias &A : M.aliases())
    if (!A.getValueType()->isFunctionTy())
      InstrumentedGlobals.insert(&A);

  bool Changed = !TaggedGlobals.empty();
  Function *MemtagLoad = nullptr;
  for (Function &F : M) {
    if (F.isDeclaration())
      continue;
    const auto &Candidates = F.hasFnAttribute(Attribute::SanitizeMemTag)
                                 ? InstrumentedGlobals
                                 : TaggedGlobals;
    if (Candidates.empty())
      continue;
    if (!MemtagLoad)
      MemtagLoad =
          Intrinsic::getOrInsertDeclaration(&M, Intrinsic::wasm_memtag_load);
    TaggedGlobalUseMaterializer(F, Candidates, MemtagLoad).run();
    Changed = true;
  }
  return Changed;
}

INITIALIZE_PASS_BEGIN(WebAssemblyGlobalsTagging, "WebAssembly-globals-tagging",
                      "WebAssembly Globals Tagging Pass", false, false)
INITIALIZE_PASS_END(WebAssemblyGlobalsTagging, "WebAssembly-globals-tagging",
                    "WebAssembly Globals Tagging Pass", false, false)

ModulePass *llvm::createWebAssemblyGlobalsTaggingPass() {
  return new WebAssemblyGlobalsTagging();
}
