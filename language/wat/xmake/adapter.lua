--- @brief Describe the core WebAssembly text assembler.
function describe()
    return {id = "wat", program = "wrwat", extensions = {".wat"}}
end

--- @brief Reject settings that would be ignored by text assembly.
function validate(target, req)
    assert(req.mte_flag ~= "--legacy-mte" and not req.std and #req.exports == 0,
           "Declare WAT exports in the source and select either strict MTE or no MTE")
    assert(not target:get("optimize") and not target:get("includedirs") and not target:get("defines"),
           "WAT assembly does not apply source optimization, includes or macros")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"), "WAT supports debug symbols")
end

--- @brief Assemble one stand-alone Core Wasm module.
function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Select one WAT source without link dependencies")
    local argv = {path.absolute(sources[1]), "--core", req.core, "--target", req.arch,
                  req.mte_flag, req.eh and "--eh" or "--no-eh", "-o", path.absolute(target:targetfile())}
    if req.threads then table.insert(argv, "--threads") end
    if req.build_receipt then table.insert(argv, "--build-receipt") end
    if target:get("symbols") then table.insert(argv, "-g") end
    for _, operation in ipairs(req.operations) do table.join2(argv, {"--ros-operation", operation}) end
    os.vrunv(req.program, argv)
end
