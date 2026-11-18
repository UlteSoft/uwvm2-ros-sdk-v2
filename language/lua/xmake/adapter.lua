function describe()
    return {id = "lua", program = "wrlua", extensions = {".lua"}}
end

function validate(target, req)
    assert(req.core == "3.0" and req.eh and req.mte and not req.threads and not req.std and #req.exports == 0,
           "Lua requires Core 3.0, EH, MTE and a single thread")
    local optimize = target:get("optimize")
    assert(not optimize or optimize == "fastest", "Lua uses -O3")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"), "Lua uses debug symbols")
    assert(not target:get("includedirs") and not target:get("defines"), "Lua cannot consume C include paths or defines")
end

function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Lua expects one application script")
    local args = {sources[1], "--target", req.arch,
                  "--toolchain", assert(os.getenv("WROS_TOOLCHAIN"), "Set WROS_TOOLCHAIN"),
                  "--sysroots", assert(os.getenv("WROS_SYSROOTS"), "Set WROS_SYSROOTS")}
    if req.lua_abi then table.insert(args, "--ros-abi") end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
