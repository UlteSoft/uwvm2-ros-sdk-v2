--- @brief Describe the AssemblyScript core Wasm compiler.
function describe()
    return {id = "as", program = "wras", extensions = {".ts"}}
end

local driver_operations = {
    ["capability.open"] = true, ["capability.close"] = true,
    ["driver.connect"] = true, ["driver.submit"] = true, ["driver.result"] = true,
    ["driver.describe"] = true, ["driver.disconnect"] = true
}

--- @brief Check the scalar profile and selected ROSv2 operations.
function validate(target, req)
    assert(req.arch == "wasm32" and not req.threads and not req.eh and req.core == "3.0",
           "AssemblyScript scalar builds require single-threaded wasm32 Core 3.0 without EH")
    assert(req.mte_flag ~= "--legacy-mte" and not req.std and #req.exports == 0,
           "AssemblyScript uses checked compiler profiles and derives exports from source")
    assert(not target:get("optimize") and not target:get("includedirs") and not target:get("defines"),
           "This AssemblyScript profile uses its fixed upstream optimizer")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"),
           "AssemblyScript accepts only the debug symbols option")
    if #req.operations ~= 1 or req.operations[1] ~= "abi" then
        for _, name in ipairs(req.operations) do
            assert(driver_operations[name], "Unsupported AssemblyScript ROSv2 operation " .. name)
        end
    end
end

--- @brief Compile the selected source and publish its core Wasm artifact.
function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Select one AssemblyScript source file")
    local argv = {path.absolute(sources[1]), req.mte_flag, "--target", req.arch, "-o", path.absolute(target:targetfile())}
    if #req.operations == 1 and req.operations[1] == "abi" then
        table.insert(argv, "--ros-abi")
    elseif #req.operations > 0 then
        table.insert(argv, "--ros-driver")
        for _, name in ipairs(req.operations) do
            table.join2(argv, {"--ros-operation", name})
        end
    end
    if req.build_receipt then table.insert(argv, "--build-receipt") end
    if target:get("symbols") then table.insert(argv, "-g") end
    os.vrunv(req.program, argv)
end
