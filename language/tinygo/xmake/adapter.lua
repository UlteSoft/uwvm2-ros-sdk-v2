function describe()
    return {id = "tinygo", program = "wrtg", extensions = {".mod"}}
end

function validate(target, req)
    assert(req.arch == "wasm32" and req.core == "3.0" and not req.threads,
           "TinyGo requires wasm32, Core 3.0 and a single thread")
    assert(not req.std and #req.exports == 0 and not target:get("includedirs") and not target:get("defines"),
           "Configure TinyGo dependencies in go.mod")
    local optimize = target:get("optimize")
    assert(not optimize or optimize == "fastest", "TinyGo builds with -O3")
    for _, symbol in ipairs(table.wrap(target:get("symbols"))) do
        assert(symbol == "debug", "TinyGo builds with debug symbols")
    end
end

function build(target, req, sources)
    assert(#sources == 1 and path.filename(sources[1]) == "go.mod" and #target:orderdeps() == 0,
           "TinyGo expects one go.mod file for the main package")
    local args = {path.directory(path.absolute(sources[1])), "--target", req.arch, "--core", req.core,
        req.eh and "--eh" or "--no-eh", req.mte_flag,
        "--toolchain", assert(os.getenv("WROS_TOOLCHAIN"), "Set WROS_TOOLCHAIN"),
        "--sysroots", assert(req.sysroots, "Set WROS_SYSROOTS to a matching receipt"),
        "--goroot", assert(os.getenv("WROS_GOROOT"), "Set WROS_GOROOT"),
        "--tinygoroot", assert(os.getenv("WROS_TINYGOROOT"), "Set WROS_TINYGOROOT")}
    if os.getenv("WROS_HOST_CXX") then table.join2(args, {"--host-cxx", os.getenv("WROS_HOST_CXX")}) end
    if req.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
