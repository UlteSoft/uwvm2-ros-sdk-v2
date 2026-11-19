--- @brief Describe the Wasm mruby frontend for installed SDK projects.
function describe()
    return {id = "ruby", program = "wrrb", extensions = {".rb"}}
end

--- @brief Check the interpreter profile and reject unrelated native options.
function validate(target, req)
    assert((req.arch == "wasm32" or req.arch == "wasm64") and req.core == "3.0" and req.eh and not req.threads and
           not req.std and #req.exports == 0, "mruby requires Core 3.0, EH and one thread")
    assert(not target:get("includedirs") and not target:get("defines"), "mruby does not consume C options")
    assert(not target:get("optimize") or target:get("optimize") == "fastest", "mruby uses -O3")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"), "mruby uses debug symbols")
end

--- @brief Build the interpreter and one Ruby application into an executable Core module.
function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "mruby expects one .rb file")
    local args = table.join({sources[1], "--target", req.arch, req.mte_flag}, req.tool_args)
    for _, operation in ipairs(req.operations) do
        table.join2(args, {"--ros-operation", operation})
    end
    if req.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(req.program, table.join(args, {"-o", target:targetfile()}))
end
