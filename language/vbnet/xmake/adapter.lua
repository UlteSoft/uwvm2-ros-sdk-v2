function describe()
    return {id = "vbnet", program = "wrvb", extensions = {".vb"}}
end

function validate(target, request)
    assert(request.kind == "binary" and request.arch == "wasm32" and request.core == "3.0" and request.eh and not request.threads,
           "Visual Basic AOT requires a final wasm32 Core 3.0 single-thread module")
    assert(request.mte_flag ~= "--legacy-mte", "Select the checked Visual Basic profile")
    assert(#request.operations == 0 or (#request.operations == 1 and (request.operations[1] == "abi" or request.operations[1] == "driver.connect")),
           "The Visual Basic scene entry accepts abi or a driver.connect binding")
    assert(#request.exports == 1 and request.exports[1]:match("^[%a_][%w_]*%.[%a_][%w_]*$"),
           "Select a Class.Method with add_wros_exports")
    local symbols = table.wrap(target:get("symbols"))
    assert(target:get("optimize") == "fastest" and #symbols == 1 and symbols[1] == "debug",
           "Visual Basic AOT requires -O3 -g")
    assert(not request.std and not request.build_receipt and not target:get("includedirs") and not target:get("defines"),
           "Unsupported Visual Basic option")
end

function build(target, request, sources)
    local args = {"--target", request.arch, request.mte_flag, request.operations[1] == "driver.connect" and "--driver-entry" or (#request.operations == 1 and "--scene-entry" or "--entry"),
                  request.exports[1], "--toolchain", assert(os.getenv("WROS_TOOLCHAIN"), "Set WROS_TOOLCHAIN to the qualified Wasm LLVM directory"),
                  "--dotnet", assert(os.getenv("WROS_DOTNET"), "Set WROS_DOTNET to the prepared host dotnet directory"), "--mono-compiler", assert(os.getenv("WROS_MONO"), "Set WROS_MONO to the prepared host compiler directory"),
                  "-o", target:targetfile()}
    table.join2(args, sources)
    os.vrunv(request.program, args)
end
