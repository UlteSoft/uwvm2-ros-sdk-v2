/** @file mark_mte.cpp
 * @brief Attach the WasmMTE function and global attributes to Flang IR.
 * @details Run before optimization, using the same LLVM API revision as
 * the final Wasm code generator. LLVM's own passes determine safe tag
 * elisions. Refuse unrelated triples, widths and user-provided inline asm.
 */
#include <llvm/Bitcode/BitcodeWriter.h>
#include <llvm/IR/Attributes.h>
#include <llvm/IR/Function.h>
#include <llvm/IR/GlobalVariable.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Verifier.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/FileSystem.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/TargetParser/Triple.h>
#include <string>
#include <string_view>

/// @brief Select a checked runtime bridge when Flang models the bounds using
/// its host's 64-bit subscript type and the guest C descriptor stores 32 bits.
static bool selectDescriptorBounds(llvm::Module &module, unsigned pointerBits) {
    for (const char *name : {"_FortranAPointerSetBounds", "_FortranAAllocatableSetBounds"}) {
        auto *function = module.getFunction(name);
        if (!function) continue;
        auto *type = function->getFunctionType();
        if (!function->isDeclaration() || type->isVarArg() || !type->getReturnType()->isVoidTy() ||
            type->getNumParams() != 4 || !type->getParamType(0)->isPointerTy() ||
            type->getParamType(0)->getPointerAddressSpace() != 0 ||
            !type->getParamType(1)->isIntegerTy(32) ||
            type->getParamType(2) != type->getParamType(3)) return false;
        if (type->getParamType(2)->isIntegerTy(pointerBits)) continue;
        if (pointerBits != 32 || !type->getParamType(2)->isIntegerTy(64)) return false;
        const std::string bridge = std::string{name} + "I64";
        if (module.getNamedValue(bridge)) return false;
        function->setName(bridge);
    }
    return true;
}

int main(int argc, char **argv) {
    if (argc != 5) return 2;
    std::string_view width{argv[1]};
    if (width != "32" && width != "64") return 2;
    const std::string_view mode{argv[2]};
    if (mode != "on" && mode != "off") return 2;
    const bool enabled = mode == "on";
    llvm::LLVMContext context;
    llvm::SMDiagnostic diagnostic;
    auto module = llvm::parseIRFile(argv[3], diagnostic, context);
    if (!module) {
        diagnostic.print("wrf", llvm::errs());
        return 1;
    }
    const auto &triple = module->getTargetTriple();
    const auto expected = width == "32" ? "wasm32-unknown-wasip1" : "wasm64-unknown-wasip1";
    if (triple.str() != expected || module->getDataLayout().getPointerSizeInBits() != (width == "32" ? 32u : 64u)
        || !module->getModuleInlineAsm().empty()) {
        llvm::errs() << "unexpected Flang target layout or module assembly\n";
        return 1;
    }
    if (!selectDescriptorBounds(*module, width == "32" ? 32 : 64)) {
        llvm::errs() << "unsupported Flang array-bound ABI\n";
        return 1;
    }
    // Only compiler-generated IR can enter this stage. Enforce the same
    // import boundary. Respect explicit function attributes, global sanitizer
    // metadata and instruction metadata produced by the language frontend.
    for (auto &fn : *module) {
        if (fn.getName().starts_with("llvm.wasm.")
            || fn.hasFnAttribute("wasm-import-module") || fn.hasFnAttribute("wasm-import-name")) {
            llvm::errs() << "unsupported target intrinsic or import override\n";
            return 1;
        }
        for (const auto &block : fn) {
            for (const auto &instruction : block) {
                const auto *call = llvm::dyn_cast<llvm::CallBase>(&instruction);
                if (call && call->isInlineAsm()) {
                    llvm::errs() << "inline assembly in Flang IR\n";
                    return 1;
                }
            }
        }
        if (enabled && !fn.isDeclaration() && !fn.hasFnAttribute(llvm::Attribute::DisableSanitizerInstrumentation))
            fn.addFnAttr(llvm::Attribute::SanitizeMemTag);
    }
    for (auto &global : module->globals()) {
        if (global.getName().starts_with("llvm.")) continue;
        llvm::GlobalValue::SanitizerMetadata meta{};
        if (global.hasSanitizerMetadata()) meta = global.getSanitizerMetadata();
        // LLVM's setNoSanitizeMetadata() sets both exclusion bits. ASan's
        // dynamic-initializer flag or a single address-sanitizer exclusion
        // on a mutable definition says nothing about its WasmMTE policy.
        const bool addToMutable = !global.isConstant() && !global.isDeclaration()
            && !meta.Memtag && !(meta.NoAddress && meta.NoHWAddress);
        if (enabled && (!global.hasSanitizerMetadata() || addToMutable)) {
            meta.Memtag = true;
            global.setSanitizerMetadata(meta);
        }
    }
    if (llvm::verifyModule(*module, &llvm::errs())) return 1;
    std::error_code error;
    llvm::raw_fd_ostream result(argv[4], error, llvm::sys::fs::OF_None);
    if (error) {
        llvm::errs() << error.message() << "\n";
        return 1;
    }
    llvm::WriteBitcodeToFile(*module, result);
    result.close();
    return result.has_error() ? 1 : 0;
}
