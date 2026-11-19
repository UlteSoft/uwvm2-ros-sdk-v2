--- @brief Describe the installed CPython Wasm compiler frontend.
function describe()
    return {id = "py", program = "wrpy", extensions = {".py"}}
end

--- @brief Refuse target profiles outside the fixed CPython port.
function validate(target, req)
    assert(req.arch == "wasm32" and req.core == "3.0" and not req.threads and not req.std and #req.exports == 0,
           "CPython requires a wasm32 Core 3.0 single-thread profile")
    assert(not target:get("includedirs") and not target:get("defines"), "CPython does not consume C options")
    assert(not target:get("optimize") or target:get("optimize") == "fastest", "CPython uses -O3")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"), "CPython uses debug symbols")
end

--- @brief Link one embedded application against the exact selected guest runtime.
function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "CPython expects one main .py file")
    local args = table.join({sources[1], "--target", req.arch, req.mte_flag, req.eh and "--eh" or "--no-eh"}, req.tool_args)
    for _, op in ipairs(req.operations) do table.join2(args, {"--ros-operation", op}) end
    for _, spec in ipairs(table.wrap(target:values("wros.py_modules"))) do
        local name, file = spec:match("^([%w_%.]+)=(.+)$")
        assert(name and file, "A Python module requires dotted.name=source.py")
        table.join2(args, {"--module", name .. "=" .. path.absolute(file, target:scriptdir())})
    end
    if req.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
