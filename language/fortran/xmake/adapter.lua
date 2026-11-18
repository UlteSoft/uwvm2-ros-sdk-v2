function describe()
    return {id = "fortran", program = "wrfortran",
            extensions = {".f", ".F", ".f90", ".F90", ".f95", ".f03", ".f08", ".f18", ".for", ".ftn"}}
end

function validate(target, req)
    assert(req.core == "3.0" and not req.threads, "The numerical Fortran route requires Core 3.0 and a single thread")
    assert(not req.std and #req.exports == 0 and not target:get("includedirs") and not target:get("defines"),
           "The numerical Fortran frontend accepts its own standard modules and exports _start")
end

function build(target, req, sources)
    local args = {"--target", req.arch, "--toolchain", assert(os.getenv("WROS_TOOLCHAIN"), "Set WROS_TOOLCHAIN"),
        "--sysroots", assert(req.sysroots, "Set WROS_SYSROOTS to a matching receipt"),
        req.mte and "--mte" or "--no-mte", req.eh and "--eh" or "--no-eh"}
    local levels = {none = "0", fast = "1", faster = "2", fastest = "3", smallest = "s"}
    table.insert(args, "-O" .. assert(levels[target:get("optimize") or "fastest"], "Unsupported optimization"))
    for _, symbol in ipairs(table.wrap(target:get("symbols"))) do
        assert(symbol == "debug", "Fortran supports debug symbols")
        table.insert(args, "-g")
    end
    for flag, variable in pairs({["--flang"] = "WROS_FLANG", ["--mte-tool"] = "WROS_FLANG_MTE_TOOL"}) do
        if os.getenv(variable) then table.join2(args, {flag, os.getenv(variable)}) end
    end
    for _, dep in ipairs(target:orderdeps()) do
        local provider = dep:data("wros.request")
        assert(provider and provider.kind == "static", "Fortran dependencies must be checked WROS static archives")
        table.join2(args, {"--link-object", dep:targetfile()})
    end
    os.vrunv(req.program, table.join(args, sources, {"-o", target:targetfile()}))
end
