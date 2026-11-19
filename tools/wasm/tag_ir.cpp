// Apply the same function and global attributes used by Clang's WasmMTE
// frontend to supported language IR before target lowering.
#include "llvm/Bitcode/BitcodeWriter.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/DebugInfo.h"
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/InlineAsm.h"
#include "llvm/IR/LLVMContext.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Verifier.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/raw_ostream.h"

// Both frontends carry the SDK's per-definition marker through IR sections.
static bool suppressMemtag(llvm::GlobalObject& object) {
    if (object.getSection() != ".wros.no_memtag") return false;
    object.setSection("");
    return true;
}

// These integer widths lower to native WebAssembly scalar registers. Wider
// values can introduce a helper call or an indirect result during legalization.
static bool isWasmRegisterInteger(llvm::Type* type) {
    const auto* integer = llvm::dyn_cast<llvm::IntegerType>(type);
    if (!integer) return false;
    const unsigned bits = integer->getBitWidth();
    return bits == 1 || bits == 8 || bits == 16 || bits == 32 || bits == 64;
}

// Rust annotations request a proof about this definition. Preserve the target
// sanitizer attribute even after proving this IR contains no linear memory:
// a later transform must still instrument any stack storage it introduces.
static bool isRegisterOnlyRustBody(const llvm::Function& function) {
    if (function.size() != 1 || function.isVarArg() ||
        !isWasmRegisterInteger(function.getReturnType())) return false;
    for (const auto& argument : function.args())
        if (!isWasmRegisterInteger(argument.getType())) return false;
    for (const auto& instruction : function.getEntryBlock()) {
        if (!llvm::isa<llvm::ReturnInst, llvm::BinaryOperator, llvm::ICmpInst,
                       llvm::SelectInst, llvm::TruncInst, llvm::ZExtInst,
                       llvm::SExtInst, llvm::FreezeInst>(instruction)) return false;
        for (const auto& operand : instruction.operands()) {
            if (!isWasmRegisterInteger(operand->getType())) return false;
            if (!llvm::isa<llvm::Argument, llvm::Instruction, llvm::ConstantInt>(operand.get()))
                return false;
        }
    }
    return true;
}

// rustc attaches a definition to an addressable source static. Do not
// re-layout anonymous constant pools, vtables or compiler-generated sections.
static bool isRustSourceConstant(const llvm::GlobalVariable& global) {
    if (global.hasSection() || global.isThreadLocal()) return false;
    llvm::SmallVector<llvm::DIGlobalVariableExpression*, 1> definitions;
    global.getDebugInfo(definitions);
    return definitions.size() == 1 && definitions.front()->getVariable()->isDefinition() &&
        definitions.front()->getExpression()->getNumElements() == 0;
}

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    llvm::StringRef mode{argv[1]};
    bool stripRustDebug = mode == "--rust-mte-strip-debug";
    bool rust = stripRustDebug || mode == "--rust-mte" || mode == "--rust-no-mte";
    if (!rust && mode != "--mte" && mode != "--no-mte") return 2;
    bool instrument = mode == "--mte" || mode == "--rust-mte" || stripRustDebug;
    llvm::LLVMContext context;
    llvm::SMDiagnostic diagnostic;
    auto module = llvm::parseIRFile(argv[2], diagnostic, context);
    if (!module) {
        diagnostic.print(argv[0], llvm::errs());
        return 1;
    }
    if (module->getTargetTriple().getArch() != llvm::Triple::wasm32 ||
        !module->getModuleInlineAsm().empty()) {
        llvm::errs() << "expected wasm32 IR without module inline assembly\n";
        return 1;
    }
    // On wasm, rustc encodes a static's link_section as a custom section
    // containing its initial bytes. It does not identify the LLVM global.
    if (rust) {
        if (auto* sections = module->getNamedMetadata("wasm.custom_sections")) {
            for (auto* entry : sections->operands()) {
                if (entry->getNumOperands() == 0) continue;
                auto* name = llvm::dyn_cast_or_null<llvm::MDString>(entry->getOperand(0));
                if (name && name->getString() == ".wros.no_memtag") {
                    llvm::errs() << "a Rust static cannot request tag elision through a Wasm custom section\n";
                    return 1;
                }
            }
        }
    }
    llvm::json::Array suppressedFunctions;
    llvm::json::Array suppressedGlobals;
    llvm::json::Array retainedFunctions;
    llvm::json::Array retainedGlobals;
    for (auto& function : *module) {
        if (function.isIntrinsic()) continue;
        function.removeFnAttr("target-cpu");
        function.removeFnAttr("target-features");
        if (function.isDeclaration()) continue;
        for (auto& block : function) {
            for (auto& instruction : block) {
                auto* call = llvm::dyn_cast<llvm::CallBase>(&instruction);
                if (call && call->isInlineAsm() &&
                    (!rust || !llvm::cast<llvm::InlineAsm>(call->getCalledOperand())->getAsmString().empty())) {
                    llvm::errs() << "inline assembly in guest IR is unsupported\n";
                    return 1;
                }
            }
        }
        const bool requested = suppressMemtag(function) ||
            function.hasFnAttribute(llvm::Attribute::DisableSanitizerInstrumentation);
        if (rust && instrument)
            function.removeFnAttr(llvm::Attribute::DisableSanitizerInstrumentation);
        if (requested && !rust) {
            suppressedFunctions.push_back(function.getName().str());
            function.removeFnAttr(llvm::Attribute::SanitizeMemTag);
            continue;
        }
        if (rust && instrument && requested) {
            auto& report = isRegisterOnlyRustBody(function) ? suppressedFunctions : retainedFunctions;
            report.push_back(function.getName().str());
        }
        if (instrument) function.addFnAttr(llvm::Attribute::SanitizeMemTag);
        else if (function.hasFnAttribute(llvm::Attribute::SanitizeMemTag)) return 1;
    }
    for (auto& global : module->globals()) {
        if (global.isDeclaration() || global.getName().starts_with("llvm.")) continue;
        if (global.isConstant()) {
            if (!rust || !instrument || !isRustSourceConstant(global)) continue;
            global.setMetadata("wasm.memtag.object", llvm::MDNode::get(context, {}));
        }
        auto metadata = global.hasSanitizerMetadata() ? global.getSanitizerMetadata()
                                                     : llvm::GlobalValue::SanitizerMetadata{};
        // setNoSanitizeMetadata records both address instrumentation exclusions.
        const bool requested = suppressMemtag(global) ||
            (rust && global.getName().starts_with("__wros_no_memtag_")) ||
            (!metadata.Memtag && metadata.NoAddress && metadata.NoHWAddress);
        if (rust && instrument && requested)
            retainedGlobals.push_back(global.getName().str());
        if (requested && !rust) {
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
    if (stripRustDebug) llvm::StripDebugInfo(*module);
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
    llvm::json::Object result{{"functions", std::move(suppressedFunctions)},
                              {"globals", std::move(suppressedGlobals)}};
    if (rust) {
        result["proof"] = "register-only-integer-ssa";
        result["retained_functions"] = std::move(retainedFunctions);
        result["retained_globals"] = std::move(retainedGlobals);
    }
    llvm::outs() << llvm::json::Value(std::move(result)) << '\n';
}
