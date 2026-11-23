// Apply the Wasm target policy to the linked TinyGo program before object
// generation. The backend lowers these sanitizer attributes into operations.
#include "llvm/Bitcode/BitcodeWriter.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/LLVMContext.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Verifier.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/raw_ostream.h"

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    llvm::StringRef mode(argv[1]);
    if (mode != "--mte" && mode != "--no-mte") return 2;
    const bool tagged = mode == "--mte";
    llvm::LLVMContext context;
    llvm::SMDiagnostic error;
    auto module = llvm::parseIRFile(argv[2], error, context);
    if (!module) {
        error.print(argv[0], llvm::errs());
        return 1;
    }
    if (module->getTargetTriple().getArch() != llvm::Triple::wasm32 ||
        !module->getModuleInlineAsm().empty()) {
        llvm::errs() << "expected wasm32 TinyGo bitcode without module assembly\n";
        return 1;
    }
    for (auto &fn : *module) {
        if (fn.isIntrinsic()) continue;
        fn.removeFnAttr("target-cpu");
        fn.removeFnAttr("target-features");
        if (fn.isDeclaration()) continue;
        for (auto &block : fn) {
            for (auto &instruction : block) {
                auto *call = llvm::dyn_cast<llvm::CallBase>(&instruction);
                if (call && call->isInlineAsm()) {
                    llvm::errs() << "cannot lower TinyGo inline assembly in " << fn.getName() << "\n";
                    return 1;
                }
            }
        }
        if (tagged) fn.addFnAttr(llvm::Attribute::SanitizeMemTag);
        else fn.removeFnAttr(llvm::Attribute::SanitizeMemTag);
    }
    for (auto &global : module->globals()) {
        if (global.isDeclaration() || global.isConstant() || global.getName().starts_with("llvm.")) continue;
        auto metadata = global.hasSanitizerMetadata() ? global.getSanitizerMetadata()
                                                     : llvm::GlobalValue::SanitizerMetadata{};
        metadata.Memtag = tagged;
        global.setSanitizerMetadata(metadata);
    }
    if (llvm::verifyModule(*module, &llvm::errs())) return 1;
    std::error_code ec;
    llvm::raw_fd_ostream output(argv[3], ec);
    if (ec) {
        llvm::errs() << ec.message() << "\n";
        return 1;
    }
    llvm::WriteBitcodeToFile(*module, output);
    output.close();
    if (output.has_error()) {
        output.clear_error();
        return 1;
    }
    return 0;
}
