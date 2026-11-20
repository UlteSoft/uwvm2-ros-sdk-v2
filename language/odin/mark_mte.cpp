/** @file
 * @brief Mark every supported Odin storage definition for the WasmMTE backend.
 * @details The driver supplies fresh IR from the pinned frontend. Reject
 * native code, optional target intrinsics and unchecked instrumentation controls.
 */
#include <llvm/ADT/SmallPtrSet.h>
#include <llvm/ADT/DenseSet.h>
#include <llvm/AsmParser/Parser.h>
#include <llvm/IR/Constants.h>
#include <llvm/Bitcode/BitcodeWriter.h>
#include <llvm/IR/DebugInfo.h>
#include <llvm/IR/DebugInfoMetadata.h>
#include <llvm/IR/Attributes.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Verifier.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/raw_ostream.h>

/// @brief Map the private source snapshot to its original location in DWARF.
static void restoreDebugPath(llvm::Module &module, llvm::StringRef original) {
    llvm::DebugInfoFinder info;
    info.processModule(module);
    llvm::SmallPtrSet<llvm::DIFile *, 8> files;
    auto remember = [&](llvm::DIFile *file) {
        if (file && (file->getFilename() == "application.odin" ||
                     file->getFilename().ends_with("/application.odin")))
            files.insert(file);
    };
    for (auto *unit : info.compile_units()) remember(unit->getFile());
    for (auto *program : info.subprograms()) remember(program->getFile());
    for (auto *scope : info.scopes()) remember(scope->getFile());
    for (auto *type : info.types()) remember(type->getFile());
    for (auto *global : info.global_variables()) remember(global->getVariable()->getFile());
    for (auto *file : files) {
        file->replaceOperandWith(0, llvm::MDString::get(module.getContext(), original));
    }
}


/// @brief Check Odin's declaration of LLVM-only runtime helper retention.
static bool knownRetention(const llvm::GlobalVariable &global) {
    if (!global.hasAppendingLinkage() || global.getSection() != "llvm.metadata" ||
        global.getAddressSpace() != 0 || global.isThreadLocal() || !global.use_empty() ||
        !global.hasInitializer() || global.hasSanitizerMetadata())
        return false;
    auto *retained = llvm::dyn_cast<llvm::ConstantArray>(global.getInitializer());
    if (!retained || retained->getNumOperands() != 5) return false;
    llvm::SmallDenseSet<llvm::StringRef, 8> expected{
        "__truncsfhf2", "__gnu_f2h_ieee", "__truncdfhf2", "__gnu_h2f_ieee", "__extendhfsf2"};
    for (const auto &operand : retained->operands()) {
        auto *helper = llvm::dyn_cast<llvm::Function>(operand.get());
        if (!helper || helper->isDeclaration() || !expected.erase(helper->getName())) return false;
    }
    return expected.empty();
}

/// @brief Preserve function-static debug records without adding them to CU globals.
static bool repairDebugGlobals(llvm::Module &module) {
    auto *units = module.getNamedMetadata("llvm.dbg.cu");
    if (!units) return false;
    for (auto *operand : units->operands()) {
        auto *unit = llvm::dyn_cast<llvm::DICompileUnit>(operand);
        if (!unit || unit->getProducer() != "odin") return false;
        llvm::SmallVector<llvm::Metadata *, 16> retained;
        for (auto *expression : unit->getGlobalVariables()) {
            if (!expression || !expression->getVariable())
                return false;
            if (!llvm::isa_and_nonnull<llvm::DILocalScope>(expression->getVariable()->getScope()))
                retained.push_back(expression);
        }
        unit->replaceGlobalVariables(llvm::DIGlobalVariableExpressionArray(
            llvm::MDTuple::get(module.getContext(), retained)));
    }
    return true;
}

int main(int argc, char **argv) {
    if (argc != 6) return 2;
    llvm::StringRef width(argv[1]);
    llvm::StringRef mode(argv[2]);
    if ((width != "32" && width != "64") || (mode != "on" && mode != "off")) return 2;
    const bool tagged = mode == "on";
    const unsigned pointerBits = width == "32" ? 32 : 64;

    llvm::LLVMContext context;
    llvm::SMDiagnostic diagnostic;
    auto parsed = llvm::parseAssemblyFileWithIndexNoUpgradeDebugInfo(
        argv[3], diagnostic, context, nullptr, [](llvm::StringRef, llvm::StringRef) { return std::nullopt; });
    auto module = std::move(parsed.Mod);
    if (!module) {
        diagnostic.print("wrodin", llvm::errs());
        return 1;
    }
    const auto target = pointerBits == 32 ? llvm::Triple::wasm32 : llvm::Triple::wasm64;
    const auto &layout = module->getDataLayout();
    if (module->getTargetTriple().getArch() != target ||
        layout.getPointerSizeInBits(0) != pointerBits || layout.getIndexSizeInBits(0) != pointerBits ||
        !module->getModuleInlineAsm().empty() || !module->ifuncs().empty()) {
        llvm::errs() << "unexpected Odin target layout or module assembly\n";
        return 1;
    }
    const auto *entry = module->getFunction("_start");
    if (!entry || entry->isDeclaration() || entry->getFunctionType()->isVarArg() ||
        !entry->arg_empty() || !entry->getReturnType()->isVoidTy()) {
        llvm::errs() << "Odin guest must define _start() -> ()\n";
        return 1;
    }
    for (auto &fn : *module) {
        if (fn.getName().starts_with("llvm.wasm.") || fn.hasPersonalityFn() ||
            fn.hasFnAttribute(llvm::Attribute::DisableSanitizerInstrumentation) ||
            fn.hasFnAttribute(llvm::Attribute::SanitizeMemTag)) {
            llvm::errs() << "unsupported Odin intrinsic or instrumentation control\n";
            return 1;
        }
        if (fn.isIntrinsic()) continue;
        fn.removeFnAttr("target-cpu");
        fn.removeFnAttr("target-features");
        // Odin runs its debug IR emission before the SDK's optimization and
        // storage instrumentation. Permit the latter on every definition.
        fn.removeFnAttr(llvm::Attribute::OptimizeNone);
        for (const auto &block : fn) {
            for (const auto &instruction : block) {
                auto *call = llvm::dyn_cast<llvm::CallBase>(&instruction);
                if ((call && call->isInlineAsm()) || instruction.getMetadata("nosanitize") ||
                    llvm::isa<llvm::AtomicRMWInst, llvm::AtomicCmpXchgInst,
                              llvm::FenceInst, llvm::InvokeInst>(instruction) ||
                    (llvm::isa<llvm::LoadInst>(instruction) && llvm::cast<llvm::LoadInst>(instruction).isAtomic()) ||
                    (llvm::isa<llvm::StoreInst>(instruction) && llvm::cast<llvm::StoreInst>(instruction).isAtomic())) {
                    llvm::errs() << "unsupported Odin assembly, memory or exception operation\n";
                    return 1;
                }
            }
        }
        if (tagged && !fn.isDeclaration()) fn.addFnAttr(llvm::Attribute::SanitizeMemTag);
    }
    for (auto &global : module->globals()) {
        if (global.getName() == "llvm.compiler.used") {
            if (!knownRetention(global)) {
                llvm::errs() << "unexpected Odin runtime metadata retention\n";
                return 1;
            }
            continue;
        }
        if (global.isDeclaration() || global.getAddressSpace() != 0 || global.isThreadLocal() ||
            global.hasSection() || global.hasSanitizerMetadata()) {
            llvm::errs() << "unsupported Odin global storage or instrumentation control\n";
            return 1;
        }
        if (tagged) {
            llvm::GlobalValue::SanitizerMetadata metadata{};
            metadata.Memtag = true;
            global.setSanitizerMetadata(metadata);
            // Constant pools and mutable definitions are both part of this
            // standalone Odin module. No foreign runtime consumes their layout.
            if (global.isConstant())
                global.setMetadata("wasm.memtag.object", llvm::MDNode::get(context, {}));
        }
    }
    if (!repairDebugGlobals(*module)) {
        llvm::errs() << "expected Odin DWARF compile-unit metadata\n";
        return 1;
    }
    restoreDebugPath(*module, argv[5]);
    if (llvm::verifyModule(*module, &llvm::errs())) return 1;
    std::error_code error;
    llvm::raw_fd_ostream output(argv[4], error);
    if (error) {
        llvm::errs() << error.message() << '\n';
        return 1;
    }
    llvm::WriteBitcodeToFile(*module, output);
    output.close();
    return output.has_error() ? 1 : 0;
}
