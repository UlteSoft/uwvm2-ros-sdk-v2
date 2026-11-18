function describe()
    return {id = "lua", program = "wrlua", extensions = {".lua"}}
end

function validate(target, req)
    assert(req.core == "3.0" and req.eh and not req.threads and not req.std and #req.exports == 0,
           "Lua requires Core 3.0, EH and a single thread")
    local optimize = target:get("optimize")
    assert(not optimize or optimize == "fastest", "Lua uses -O3")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"), "Lua uses debug symbols")
    assert(not target:get("includedirs") and not target:get("defines"), "Lua cannot consume C include paths or defines")
end

function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Lua expects one application script")
    local args = table.join({sources[1], "--target", req.arch, req.mte_flag}, req.tool_args)
    if req.lua_seed then table.insert(args, "--guest-seed"); table.insert(args, req.lua_seed) end
    if req.lua_abi then table.insert(args, "--ros-abi") end
    for _, name in ipairs(req.lua_operations) do
        table.insert(args, "--ros-operation")
        table.insert(args, name)
    end
    if req.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
