function describe()
    return {id = "rs", program = "wrrust", extensions = {".rs"}}
end

function validate(target, req)
    assert(req.arch == "wasm32" and req.core == "3.0" and not req.eh and not req.threads,
           "Rust no_std requires wasm32, Core 3.0, panic=abort and one thread")
    assert(not req.std and #req.exports == 0 and not target:get("includedirs") and not target:get("defines"),
           "Rust accepts one edition-2024 crate root with _start")
end

function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Rust expects a single crate root with its Rust modules")
    local args = {path.absolute(sources[1]), "--target", req.arch, "--core", req.core, "--no-eh",
        "--rustroot", assert(os.getenv("WROS_RUSTROOT"), "Set WROS_RUSTROOT to the pinned rustc prefix"),
        "--toolchain", assert(os.getenv("WROS_TOOLCHAIN"), "Set WROS_TOOLCHAIN"),
        "--sysroots", assert(req.sysroots, "Set WROS_SYSROOTS to the matching build receipt"),
        req.mte and "--mte" or "--no-mte"}
    local levels = {none = "0", fast = "1", faster = "2", fastest = "3"}
    table.insert(args, "-O" .. assert(levels[target:get("optimize") or "faster"], "Unsupported Rust optimization"))
    for _, symbol in ipairs(table.wrap(target:get("symbols"))) do
        assert(symbol == "debug", "Rust supports debug symbols")
        table.insert(args, "-g")
    end
    if os.getenv("WROS_HOST_CXX") then table.join2(args, {"--host-cxx", os.getenv("WROS_HOST_CXX")}) end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
