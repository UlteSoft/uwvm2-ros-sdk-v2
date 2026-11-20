--- @brief Describe the AssemblyScript core Wasm compiler.
function describe()
    return {id = "as", program = "wras", extensions = {".ts"}}
end

--- @brief Check the scalar profile and the selected ROSv2 operation.
function validate(target, req)
    assert(req.arch == "wasm32" and not req.threads and not req.eh and req.core == "3.0",
           "AssemblyScript scalar builds require single-threaded wasm32 Core 3.0 without EH")
    assert(req.mte_flag ~= "--legacy-mte" and not req.std and #req.exports == 0,
           "AssemblyScript verifies memory-free output and derives exports from source")
    assert(not target:get("optimize") and not target:get("includedirs") and not target:get("defines"),
           "This AssemblyScript profile uses its fixed upstream optimizer")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"),
           "AssemblyScript accepts only the debug symbols option")
    assert(#req.operations == 0 or (#req.operations == 1 and req.operations[1] == "abi"),
           "This AssemblyScript profile accepts only the optional ROSv2 abi operation")
end

--- @brief Compile the selected source and publish its core Wasm artifact.
function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Select one AssemblyScript source file")
    local argv = {path.absolute(sources[1]), req.mte_flag, "--target", req.arch, "-o", path.absolute(target:targetfile())}
    if #req.operations > 0 then table.insert(argv, "--ros-abi") end
    if req.build_receipt then table.insert(argv, "--build-receipt") end
    if target:get("symbols") then table.insert(argv, "-g") end
    os.vrunv(req.program, argv)
end
