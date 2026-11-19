function describe()
    return {id = "rs", program = "wrrs", extensions = {".rs"}}
end

function validate(target, req)
    assert(req.arch == "wasm32" and req.core == "3.0" and not req.eh and not req.threads,
           "Rust no_std requires wasm32, Core 3.0, panic=abort and one thread")
    assert(not req.std and #req.exports == 0 and not target:get("includedirs") and not target:get("defines"),
           "Rust accepts one edition-2024 crate root with _start")
end

function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Rust expects a single crate root with its Rust modules")
    local args = {path.absolute(sources[1]), "--target", req.arch, "--core", req.core, "--no-eh", req.mte_flag}
    local rust = os.getenv("WROS_RUSTROOT")
    local tool = os.getenv("WROS_TOOLCHAIN")
    local cxx = os.getenv("WROS_HOST_CXX")
    if rust or tool or req.sysroots or cxx then
        assert(rust and tool and req.sysroots, "Set WROS_RUSTROOT, WROS_TOOLCHAIN and WROS_SYSROOTS together")
        table.join2(args, {"--rustroot", rust, "--toolchain", tool, "--sysroots", req.sysroots})
        if cxx then table.join2(args, {"--host-cxx", cxx}) end
    end
    local optimize = target:get("optimize")
    if optimize then
        local levels = {none = "0", fast = "1", faster = "2", fastest = "3"}
        table.insert(args, "-O" .. assert(levels[optimize], "Unsupported Rust optimization"))
    end
    for _, symbol in ipairs(table.wrap(target:get("symbols"))) do
        assert(symbol == "debug", "Rust supports debug symbols")
        table.insert(args, "-g")
    end
    if req.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
