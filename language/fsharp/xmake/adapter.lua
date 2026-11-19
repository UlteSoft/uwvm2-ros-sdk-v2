function describe()
    return {id = "fsharp", program = "wrfs", extensions = {".fs"}}
end

function validate(target, request)
    assert(request.kind == "binary" and request.arch == "wasm32" and request.core == "3.0" and not request.threads,
           "F# AOT requires a final wasm32 Core 3.0 single-thread module")
    assert(request.mte_flag ~= "--legacy-mte", "Select the checked F# profile")
    assert(#request.operations == 0 or (#request.operations == 1 and request.operations[1] == "abi"),
           "The F# scene entry accepts only the abi operation")
    assert(#request.exports == 1 and request.exports[1]:match("^[%a_][%w_]*%.[%a_][%w_]*$"),
           "Select a Class.Method with add_wros_exports")
    local symbols = table.wrap(target:get("symbols"))
    assert(target:get("optimize") == "fastest" and #symbols == 1 and symbols[1] == "debug",
           "F# AOT requires -O3 -g")
    assert(not request.std and not request.build_receipt and not target:get("includedirs") and not target:get("defines"),
           "Unsupported F# option")
end

function build(target, request, sources)
    local args = {"--target", request.arch, request.eh and "--eh" or "--no-eh", request.mte_flag, #request.operations == 1 and "--scene-entry" or "--entry",
                  request.exports[1], "--toolchain", assert(os.getenv("WROS_TOOLCHAIN")),
                  "--dotnet", assert(os.getenv("WROS_DOTNET")), "--mono-compiler", assert(os.getenv("WROS_MONO")),
                  "-o", target:targetfile()}
    table.join2(args, sources)
    os.vrunv(request.program, args)
end
