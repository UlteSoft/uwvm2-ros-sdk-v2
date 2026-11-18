function describe()
    return {id = "d", program = "wrd", extensions = {".d"}}
end

function validate(target, request)
    assert(request.kind == "binary" and request.arch == "wasm32" and request.core == "3.0" and
           request.eh and request.mte_flag == "--mte" and not request.threads, "D BetterC requires signed wasm32 Core 3 EH with MTE")
    assert(not request.std and #request.exports == 0 and not target:get("includedirs") and not target:get("defines"),
           "D BetterC uses its signed imports and exports _start")
    assert(not target:get("optimize") or target:get("optimize") == "fastest", "D BetterC requires -O3")
    for _, symbol in ipairs(table.wrap(target:get("symbols"))) do
        assert(symbol == "debug", "D BetterC requires debug symbols")
    end
end

function build(target, request, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Select one BetterC application source")
    local args = {sources[1], "-o", target:targetfile()}
    if request.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(request.program, args)
end
