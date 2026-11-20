--- @brief Describe the standalone Odin Core Wasm frontend.
function describe()
    return {id = "odin", program = "wrodin", extensions = {".odin"}}
end

--- @brief Restrict the Wasm target to the reviewed Odin profile.
function validate(target, req)
    assert(req.arch == "wasm32" and req.core == "3.0" and not req.eh and not req.threads and not req.std,
           "Odin requires single-threaded wasm32 Core 3.0 without EH")
    assert(req.mte_flag ~= "--legacy-mte" and #req.exports == 0,
           "Odin derives exports from source and accepts the tagged and untagged profiles")
    assert(#req.operations == 0 or (#req.operations == 1 and req.operations[1] == "abi"),
           "Odin accepts only the optional ROSv2 abi operation")
    assert(not target:get("includedirs") and not target:get("defines"), "Odin does not use C options")
    assert(not target:get("optimize") or target:get("optimize") == "fastest", "Odin builds use -O3")
    local symbols = table.wrap(target:get("symbols"))
    assert(#symbols == 0 or (#symbols == 1 and symbols[1] == "debug"), "Odin retains debugging information")
end

--- @brief Compile a freestanding Odin source with the selected Wasm tools.
function build(target, req, sources)
    assert(#sources == 1 and #target:orderdeps() == 0, "Select one Odin source file and no foreign objects")
    local toolchain = os.getenv("WROS_TOOLCHAIN")
    assert(toolchain and req.sysroots, "Provide WROS_TOOLCHAIN and matching WROS_SYSROOTS for Odin")
    local args = {path.absolute(sources[1]), "--target", req.arch, req.mte_flag, "--toolchain", toolchain,
                  "--sysroots", req.sysroots, "-o", path.absolute(target:targetfile())}
    if #req.operations == 1 then table.insert(args, "--ros-abi") end
    if req.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(req.program, args)
end
