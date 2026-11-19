--- @brief Describe the standard Go compiler's scalar Wasm input.
function describe()
    return {id = "go", program = "wrgo", extensions = {".go"}}
end

--- @brief Check the scalar profile and its optional ROS ABI import during configuration.
function validate(target, req)
    assert(req.arch == "wasm32" and not req.threads and req.core == "3.0",
           "The standard Go scalar package requires single-threaded wasm32 Core 3.0")
    assert(req.mte_flag ~= "--legacy-mte" and not req.std and #req.exports == 0,
           "Standard Go verifies register-only functions and derives exports from the Go source")
    assert(not target:get("optimize") and not target:get("includedirs") and not target:get("defines"),
           "Standard Go uses its fixed optimized scalar producer")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"),
           "Standard Go accepts only source-level debug symbols")
    assert(#req.operations == 0 or (#req.operations == 1 and req.operations[1] == "abi"),
           "The scalar Go profile accepts only the optional ROSv2 abi operation")
end

--- @brief Build a core module using the selected installation and exact authority declaration.
function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Select one Go source file")
    local argv = {path.absolute(sources[1]), req.mte_flag, "--target", req.arch, "-o", path.absolute(target:targetfile())}
    if #req.operations > 0 then table.insert(argv, "--ros-abi") end
    if req.build_receipt then table.insert(argv, "--build-receipt") end
    if target:get("symbols") then table.insert(argv, "-g") end
    os.vrunv(req.program, argv)
end
