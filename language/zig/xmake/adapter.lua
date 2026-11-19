--- @brief Describe the standalone Core Wasm Zig frontend.
function describe()
    return {id = "zig", program = "wrzig", extensions = {".zig"}}
end

--- @brief Enforce the reviewed single-threaded, non-exception Zig ABI.
function validate(target, req)
    assert((req.arch == "wasm32" or req.arch == "wasm64") and req.core == "3.0" and not req.eh and
           not req.threads and not req.std and #req.exports == 0 and #req.operations == 0,
           "Zig requires Core 3.0, no EH, one thread, and explicit extern declarations in source")
    assert(not target:get("includedirs") and not target:get("defines"), "Zig does not consume C options")
    assert(not target:get("optimize") or target:get("optimize") == "fastest", "Zig uses -O3")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"), "Zig retains debug symbols")
end

--- @brief Compile one source unit without admitting foreign libraries.
function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Zig expects one .zig source and no foreign objects")
    local args = table.join({sources[1], "--target", req.arch, req.mte_flag}, req.tool_args)
    if req.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
