function describe()
    return {id = "nim", program = "wrnim", extensions = {".nim"}}
end

function validate(target, request)
    assert(request.core == "3.0" and not request.threads, "The standalone Nim ARC profile uses Core 3.0 and a single thread")
    assert(not request.std and #request.exports == 0 and not target:get("includedirs") and not target:get("defines"),
           "The Nim application exports _start and uses the selected guest library")
end

function build(target, request, sources)
    assert(#sources == 1, "Select one Nim application. Import its other modules in the entry file.")
    local levels = {none = "0", fast = "1", faster = "2", fastest = "3", smallest = "s"}
    local args = {sources[1], "--target", request.arch, "--toolchain", assert(os.getenv("WROS_TOOLCHAIN")),
                  "--sysroots", assert(request.sysroots), "--producer", assert(os.getenv("WROS_NIM_PRODUCER")),
                  request.eh and "--eh" or "--no-eh", request.mte_flag,
                  "-O" .. assert(levels[target:get("optimize") or "faster"])}
    for _, symbol in ipairs(table.wrap(target:get("symbols"))) do
        assert(symbol == "debug", "Unsupported Nim symbols mode")
        table.insert(args, "-g")
    end
    if request.build_receipt then table.insert(args, "--build-receipt") end
    os.vrunv(request.program, table.join(args, {"-o", target:targetfile()}))
end
