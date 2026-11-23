// WROS additions, applied to Rust IR before either LLVM optimization pipeline.
// Plain upstream rustc compilations do not set this option.
#include "llvm/IR/DebugInfo.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/InlineAsm.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Module.h"
#include "llvm/Support/CommandLine.h"

static llvm::cl::opt<std::string> WrosIRMode(
    "wros-ir", llvm::cl::Hidden, llvm::cl::init(""),
    llvm::cl::desc("Prepare rustc Wasm IR for the WROS LLVM lowering pass"));

static bool wrosSourceConstant(const llvm::GlobalVariable &Global) {
  if (Global.hasSection() || Global.isThreadLocal())
    return false;
  llvm::SmallVector<llvm::DIGlobalVariableExpression *, 1> Definitions;
  Global.getDebugInfo(Definitions);
  return Definitions.size() == 1 &&
         Definitions.front()->getVariable()->isDefinition() &&
         Definitions.front()->getExpression()->getNumElements() == 0;
}

// Return a diagnostic for unsupported IR. Do not allow a source annotation
// to exempt the storage in a Rust definition from the selected MTE policy.
static const char *wrosPrepareIR(llvm::Module &Module, bool NoDefaultPasses) {
  llvm::StringRef Mode = WrosIRMode.getValue();
  if (Mode.empty())
    return nullptr;
  if (Mode != "plain" && Mode != "mte" && Mode != "mte-strip-debug")
    return "unknown WROS Rust IR mode";
  if (!NoDefaultPasses || !Module.getTargetTriple().isWasm() ||
      !Module.getModuleInlineAsm().empty())
    return "WROS Rust requires unoptimized WebAssembly IR without module assembly";
  bool Mte = Mode != "plain";
  if (auto *Sections = Module.getNamedMetadata("wasm.custom_sections"))
    for (auto *Entry : Sections->operands()) {
      if (Entry->getNumOperands() == 0)
        continue;
      auto *Name = llvm::dyn_cast_or_null<llvm::MDString>(Entry->getOperand(0));
      if (Name && Name->getString() == ".wros.no_memtag")
        return "Rust statics cannot request tag elision through a custom section";
    }
  for (auto &F : Module) {
    if (F.isIntrinsic())
      continue;
    F.removeFnAttr("target-cpu");
    F.removeFnAttr("target-features");
    if (F.isDeclaration())
      continue;
    for (auto &B : F)
      for (auto &I : B)
        if (auto *Call = llvm::dyn_cast<llvm::CallBase>(&I))
          if (Call->isInlineAsm() &&
              !llvm::cast<llvm::InlineAsm>(Call->getCalledOperand())->getAsmString().empty())
            return "inline assembly in Rust guest IR is unsupported";
    if (F.getSection() == ".wros.no_memtag")
      F.setSection("");
    if (Mte) {
      F.removeFnAttr(llvm::Attribute::DisableSanitizerInstrumentation);
      F.addFnAttr(llvm::Attribute::SanitizeMemTag);
    } else if (F.hasFnAttribute(llvm::Attribute::SanitizeMemTag)) {
      return "unexpected sanitize_memtag attribute in a plain Rust guest";
    }
  }
  for (auto &G : Module.globals()) {
    if (G.isDeclaration() || G.getName().starts_with("llvm."))
      continue;
    if (G.getSection() == ".wros.no_memtag")
      G.setSection("");
    if (G.isConstant()) {
      if (!Mte || !wrosSourceConstant(G))
        continue;
      G.setMetadata("wasm.memtag.object", llvm::MDNode::get(Module.getContext(), {}));
    }
    auto Metadata = G.hasSanitizerMetadata() ? G.getSanitizerMetadata()
                                             : llvm::GlobalValue::SanitizerMetadata{};
    if (Mte) {
      Metadata.Memtag = true;
      G.setSanitizerMetadata(Metadata);
    } else if (Metadata.Memtag) {
      return "unexpected memtag global in a plain Rust guest";
    }
  }
  if (Mode == "mte-strip-debug")
    llvm::StripDebugInfo(Module);
  return nullptr;
}
