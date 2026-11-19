/** @file
 * @brief Mark every supported Zig storage definition for the WasmMTE backend.
 * @details The driver supplies fresh IR from the pinned frontend. Reject
 * native code, optional target intrinsics and unchecked instrumentation controls.
 */
#include <llvm/Bitcode/BitcodeWriter.h>
#include <llvm/IR/Attributes.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Verifier.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/raw_ostream.h>

int main(int argc, char **argv) {
    if (argc != 5) return 2;
    llvm::StringRef width(argv[1]);
    llvm::StringRef mode(argv[2]);
    if ((width != "32" && width != "64") || (mode != "on" && mode != "off")) return 2;
    const bool tagged = mode == "on";
    const unsigned pointerBits = width == "32" ? 32 : 64;

    llvm::LLVMContext context;
    llvm::SMDiagnostic diagnostic;
    auto module = llvm::parseIRFile(argv[3], diagnostic, context);
    if (!module) {
        diagnostic.print("wrzig", llvm::errs());
        return 1;
    }
    const auto expected = pointerBits == 32 ? llvm::Triple::wasm32 : llvm::Triple::wasm64;
    if (module->getTargetTriple().getArch() != expected ||
        module->getDataLayout().getPointerSizeInBits() != pointerBits ||
        !module->getModuleInlineAsm().empty() || !module->ifuncs().empty()) {
        llvm::errs() << "unexpected Zig target layout or module assembly\n";
        return 1;
    }
    for (auto &fn : *module) {
        if (fn.getName().starts_with("llvm.wasm.") || fn.hasPersonalityFn() ||
            fn.hasFnAttribute(llvm::Attribute::DisableSanitizerInstrumentation) ||
            fn.hasFnAttribute(llvm::Attribute::SanitizeMemTag)) {
            llvm::errs() << "unsupported Zig intrinsic or instrumentation control\n";
            return 1;
        }
        if (fn.isIntrinsic()) continue;
        fn.removeFnAttr("target-cpu");
        fn.removeFnAttr("target-features");
        // Zig runs its debug IR emission before the SDK's optimization and
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
                    llvm::errs() << "unsupported Zig assembly, memory or exception operation\n";
                    return 1;
                }
            }
        }
        if (tagged && !fn.isDeclaration()) fn.addFnAttr(llvm::Attribute::SanitizeMemTag);
    }
    for (auto &global : module->globals()) {
        if (global.isDeclaration() || global.getAddressSpace() != 0 || global.isThreadLocal() ||
            global.hasSection() || global.hasSanitizerMetadata()) {
            llvm::errs() << "unsupported Zig global storage or instrumentation control\n";
            return 1;
        }
        if (tagged) {
            llvm::GlobalValue::SanitizerMetadata metadata{};
            metadata.Memtag = true;
            global.setSanitizerMetadata(metadata);
            // Constant pools and mutable definitions are both part of this
            // standalone Zig module. No foreign runtime consumes their layout.
            if (global.isConstant())
                global.setMetadata("wasm.memtag.object", llvm::MDNode::get(context, {}));
        }
    }
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
