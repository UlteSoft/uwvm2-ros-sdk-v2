// Extract the MethodDef selected by the metadata reader from Mono's actual
// method table. Rebuild the external ABI with one argument. Code that uses the
// CLR context, globals, other calls or external state cannot form this module.
#include "llvm/Bitcode/BitcodeWriter.h"
#include "llvm/BinaryFormat/Dwarf.h"
#include "llvm/IR/DIBuilder.h"
#include "llvm/Support/Path.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Verifier.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Transforms/Utils/Cloning.h"

static int reject(llvm::StringRef reason) {
    llvm::errs() << reason << '\n';
    return 1;
}

int main(int argc, char** argv) {
    if (argc != 9) return 2;
    llvm::StringRef mode(argv[1]);
    unsigned row{};
    if ((mode != "--mte" && mode != "--no-mte") || llvm::StringRef(argv[2]).getAsInteger(10, row)) return 2;
    llvm::LLVMContext context;
    llvm::SMDiagnostic error;
    auto source = llvm::parseIRFile(argv[3], error, context);
    if (!source) {
        error.print(argv[0], llvm::errs());
        return 1;
    }
    if (source->getTargetTriple().getArch() != llvm::Triple::wasm32 || !source->getModuleInlineAsm().empty())
        return reject("expected Mono core wasm32 IR");
    auto* table = source->getNamedGlobal("mono_aot_WrosKernel_method_table");
    auto* entries = table && table->hasInitializer() ? llvm::dyn_cast<llvm::ConstantArray>(table->getInitializer()) : nullptr;
    auto* original = entries && row < entries->getNumOperands() ? llvm::dyn_cast<llvm::Function>(entries->getOperand(row)) : nullptr;
    if (!original || original->isDeclaration() || original->isVarArg() || !original->getReturnType()->isIntegerTy(32) ||
        original->arg_size() != 2 || !original->getArg(0)->getType()->isIntegerTy(32) ||
        !original->getArg(1)->getType()->isPointerTy() || !original->getArg(1)->use_empty())
        return reject("Mono entry needs an unsupported ABI or CLR context");
    for (auto& block : *original)
        for (auto& instruction : block) {
            if (llvm::isa<llvm::CallBase>(instruction)) return reject("numeric method uses an external call");
            for (auto& operand : instruction.operands())
                if (auto* value = llvm::dyn_cast<llvm::Constant>(operand.get());
                    value && !llvm::isa<llvm::ConstantData, llvm::ConstantPointerNull>(value))
                    return reject("numeric method references external state");
        }
    llvm::Module guest("numeric", context);
    guest.setTargetTriple(source->getTargetTriple());
    guest.setDataLayout(source->getDataLayout());
    auto* int32 = llvm::Type::getInt32Ty(context);
    auto* entry = llvm::Function::Create(llvm::FunctionType::get(int32, {int32}, false),
                                         llvm::GlobalValue::ExternalLinkage, "evaluate", guest);
    llvm::ValueToValueMapTy mapping;
    mapping[original->getArg(0)] = entry->getArg(0);
    mapping[original->getArg(1)] = llvm::ConstantPointerNull::get(llvm::PointerType::getUnqual(context));
    llvm::SmallVector<llvm::ReturnInst*, 4> returns;
    llvm::CloneFunctionInto(entry, original, mapping, llvm::CloneFunctionChangeType::DifferentModule, returns);
    entry->setAttributes(llvm::AttributeList{});
    if (mode == "--mte") entry->addFnAttr(llvm::Attribute::SanitizeMemTag);
    unsigned line{}, points{};
    if (llvm::StringRef(argv[7]).getAsInteger(10, line) || llvm::StringRef(argv[8]).getAsInteger(10, points)) return 2;
    llvm::StringRef fileName(argv[6]);
    if (!fileName.empty() && line && points) {
        guest.addModuleFlag(llvm::Module::Warning, "Debug Info Version", llvm::DEBUG_METADATA_VERSION);
        guest.addModuleFlag(llvm::Module::Warning, "Dwarf Version", 4);
        llvm::DIBuilder di(guest);
        auto* file = di.createFile(llvm::sys::path::filename(fileName), llvm::sys::path::parent_path(fileName));
        // This LLVM release has no DW_LANG code for F#. Preserve its actual
        // source name and producer without identifying the source language as C#.
        bool fsharp = fileName.ends_with_insensitive(".fs");
        unsigned language = fsharp ? 0 : llvm::dwarf::DW_LANG_C_sharp;
        di.createCompileUnit(language, file, fsharp ? "WasmROS F# + Mono LLVMOnly" : "WasmROS Roslyn + Mono LLVMOnly",
                             true, "-O3 -g", 0);
        auto* integer = di.createBasicType("int", 32, llvm::dwarf::DW_ATE_signed);
        auto* signature = di.createSubroutineType(di.getOrCreateTypeArray({integer, integer}));
        auto* sp = di.createFunction(file, argv[5], "evaluate", file, line, signature, points == 1 ? line : 0, llvm::DINode::FlagZero,
                                     llvm::DISubprogram::SPFlagDefinition | llvm::DISubprogram::SPFlagOptimized);
        entry->setSubprogram(sp);
        for (auto& block : *entry)
            for (auto& instruction : block)
                instruction.setDebugLoc(llvm::DILocation::get(context, points == 1 ? line : 0, 0, sp));
        di.finalize();
    }
    if (llvm::verifyModule(guest, &llvm::errs())) return 1;
    std::error_code ec;
    llvm::raw_fd_ostream out(argv[4], ec);
    if (ec) return reject(ec.message());
    llvm::WriteBitcodeToFile(guest, out);
    out.close();
    if (out.has_error()) {
        out.clear_error();
        return reject("failed to write numeric bitcode");
    }
    return 0;
}
