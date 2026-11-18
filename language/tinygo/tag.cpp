// Apply the same function and global attributes used by Clang's WasmMTE
// frontend to all live TinyGo program and runtime code before target lowering.
#include "llvm/Bitcode/BitcodeWriter.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/LLVMContext.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Verifier.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/raw_ostream.h"

// TinyGo carries //go:section on the LLVM definition and prevents a marked
// function from being inlined before this stage. Consume the SDK marker here.
static bool suppressMemtag(llvm::GlobalObject& object) {
    if (object.getSection() != ".wros.no_memtag") return false;
    object.setSection("");
    return true;
}

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    llvm::StringRef mode{argv[1]};
    if (mode != "--mte" && mode != "--no-mte") return 2;
    bool instrument = mode == "--mte";
    llvm::LLVMContext context;
    llvm::SMDiagnostic diagnostic;
    auto module = llvm::parseIRFile(argv[2], diagnostic, context);
    if (!module) {
        diagnostic.print(argv[0], llvm::errs());
        return 1;
    }
    if (module->getTargetTriple().getArch() != llvm::Triple::wasm32 ||
        !module->getModuleInlineAsm().empty()) {
        llvm::errs() << "expected wasm32 TinyGo IR without inline assembly\n";
        return 1;
    }
    llvm::json::Array suppressedFunctions;
    llvm::json::Array suppressedGlobals;
    for (auto& function : *module) {
        if (function.isIntrinsic()) continue;
        function.removeFnAttr("target-cpu");
        function.removeFnAttr("target-features");
        if (function.isDeclaration()) continue;
        for (auto& block : function) {
            for (auto& instruction : block) {
                auto* call = llvm::dyn_cast<llvm::CallBase>(&instruction);
                if (call && call->isInlineAsm()) {
                    llvm::errs() << "inline assembly in TinyGo IR is unsupported\n";
                    return 1;
                }
            }
        }
        if (suppressMemtag(function) || function.hasFnAttribute(llvm::Attribute::DisableSanitizerInstrumentation)) {
            suppressedFunctions.push_back(function.getName().str());
            function.removeFnAttr(llvm::Attribute::SanitizeMemTag);
            continue;
        }
        if (instrument) function.addFnAttr(llvm::Attribute::SanitizeMemTag);
        else if (function.hasFnAttribute(llvm::Attribute::SanitizeMemTag)) return 1;
    }
    for (auto& global : module->globals()) {
        if (global.isDeclaration() || global.isConstant() || global.getName().starts_with("llvm.")) continue;
        auto metadata = global.hasSanitizerMetadata() ? global.getSanitizerMetadata()
                                                     : llvm::GlobalValue::SanitizerMetadata{};
        // setNoSanitizeMetadata records both address instrumentation exclusions.
        if (suppressMemtag(global) || (!metadata.Memtag && metadata.NoAddress && metadata.NoHWAddress)) {
            suppressedGlobals.push_back(global.getName().str());
            metadata.Memtag = false;
            global.setSanitizerMetadata(metadata);
            continue;
        }
        if (instrument) {
            metadata.Memtag = true;
            global.setSanitizerMetadata(metadata);
        } else if (metadata.Memtag) {
            return 1;
        }
    }
    if (llvm::verifyModule(*module, &llvm::errs())) return 1;
    std::error_code error;
    llvm::raw_fd_ostream out(argv[3], error);
    if (error) {
        llvm::errs() << error.message() << '\n';
        return 1;
    }
    llvm::WriteBitcodeToFile(*module, out);
    out.close();
    if (out.has_error()) {
        llvm::errs() << "failed to write instrumented bitcode\n";
        out.clear_error();
        return 1;
    }
    llvm::outs() << llvm::json::Value(llvm::json::Object{
        {"functions", std::move(suppressedFunctions)}, {"globals", std::move(suppressedGlobals)}
    }) << '\n';
}
