function describe()
    return {id = "csharp", program = "wrcs", static = true, extensions = {".cs"}}
end

function validate(target, request)
    assert(request.arch == "wasm32" and request.core == "3.0" and request.eh and not request.threads,
           "C# numeric AOT requires wasm32 Core 3.0, single-thread with the standard EH target")
    assert(request.mte_flag == "--legacy-mte" or request.mte_flag == "--no-mte",
           "C# numeric AOT has no signed strict MTE release")
    local exports = request.exports
    assert(#exports == 1 and exports[1]:match("^[%a_][%w_]*%.[%a_][%w_]*$"),
           "add_wros_exports must select exactly one C# Class.Method")
    local symbols = table.wrap(target:get("symbols"))
    assert(target:get("optimize") == "fastest" and #symbols == 1 and symbols[1] == "debug",
           "C# numeric AOT requires -O3 -g")
    assert(not request.std and not request.build_receipt and not target:get("includedirs") and not target:get("defines"),
           "Unsupported C# numeric build options")
end

function build(target, request, sources)
    local output = target:targetfile()
    if request.kind == "static" then
        assert(#target:orderdeps() == 0, "The C# numeric static producer accepts source files only")
        output = path.join(target:autogendir(), "wros", "evaluate.o")
        os.mkdir(path.directory(output))
    end
    local args = {"--target", request.arch, request.mte_flag, "--entry", request.exports[1],
                  "--toolchain", assert(os.getenv("WROS_TOOLCHAIN")),
                  "--dotnet", assert(os.getenv("WROS_DOTNET")),
                  "--mono-compiler", assert(os.getenv("WROS_MONO")), "-o", output}
    if request.kind == "static" then
        table.join2(args, {"-c", "--sysroots", assert(request.sysroots, "Set WROS_SYSROOTS for a C# object")})
    end
    table.join2(args, sources)
    os.vrunv(request.program, args)
    if request.kind == "static" then
        os.vrunv(path.join(request.root, "bin/wrar"), {"--toolchain", os.getenv("WROS_TOOLCHAIN"), "-o", target:targetfile(), output})
    end
end
