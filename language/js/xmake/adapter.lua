function describe()
    return {id = "js", program = "wrjs", extensions = {".js"}}
end

function validate(target, req)
    assert(req.arch == "wasm32" and req.core == "3.0" and req.eh and not req.threads and
           not req.std and #req.exports == 0, "QuickJS requires wasm32 Core 3.0, EH and one thread")
    assert(not target:get("includedirs") and not target:get("defines"), "QuickJS does not consume C options")
    assert(not target:get("optimize") or target:get("optimize") == "fastest", "QuickJS uses -O3")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"), "QuickJS uses debug symbols")
end

function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "QuickJS expects one .js file")
    local args = table.join({sources[1], "--target", req.arch, req.mte_flag}, req.tool_args)
    for _, op in ipairs(req.operations) do
        table.insert(args, "--ros-operation"); table.insert(args, op)
    end
    if req.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
