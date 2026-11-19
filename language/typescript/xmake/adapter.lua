--- @file adapter.lua
--- @brief Configure and build closed-source-set TypeScript Wasm applications.
--- @return The SDK language identity, compiler and accepted file extension.
function describe()
    return {id = "typescript", program = "wrts", extensions = {".ts"}}
end

--- @brief Validate the target against the signed interpreter profile.
function validate(target, req)
    assert(req.arch == "wasm32" and req.core == "3.0" and req.eh and not req.threads and
           not req.std and #req.exports == 0, "TypeScript requires wasm32 Core 3.0, EH and one thread")
    assert(not target:get("includedirs") and not target:get("defines"), "TypeScript sources do not take C options")
    assert(not target:get("optimize") or target:get("optimize") == "fastest", "the embedded interpreter uses -O3")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"), "the embedded interpreter uses debug symbols")
end

--- @brief Compile each declared module under the selected project entry and operation policy.
function build(target, req, sources)
    assert(#target:orderdeps() == 0, "declare TypeScript project modules with add_files")
    local inputs = {}
    local entry = target:values("wros.typescript_entry")
    if entry then
        for _, file in ipairs(sources) do
            if path.absolute(file) == path.absolute(entry) then table.insert(inputs, file) end
        end
        assert(#inputs == 1, "TypeScript entry must occur once in add_files")
    else
        assert(#sources == 1, "set_wros_typescript_entry selects the startup module in a multi-file project")
        table.insert(inputs, sources[1])
    end
    for _, file in ipairs(sources) do
        if file ~= inputs[1] then table.insert(inputs, file) end
    end
    local args = table.join(inputs, {"--target", req.arch, req.mte_flag, "--project-root", os.projectdir()}, req.tool_args)
    for _, name in ipairs(req.operations) do
        table.join2(args, {"--ros-operation", name})
    end
    if req.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
