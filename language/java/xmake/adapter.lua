function describe()
    return {id = "java", program = "wrjava", extensions = {".java"}}
end

function validate(target, request)
    assert(request.arch == "wasm32" and request.core == "3.0" and request.eh and not request.threads,
           "The synchronous JVM route requires wasm32 Core 3.0, one thread, and an EH sysroot")
    assert(request.mte_flag ~= "--no-mte", "The synchronous JVM route has no uninstrumented release")
    local symbols = table.wrap(target:get("symbols"))
    assert(target:get("optimize") == "fastest" and #symbols == 1 and symbols[1] == "debug",
           "The synchronous JVM route builds with -O3 -g")
    assert(not request.std and #request.exports == 0 and not request.build_receipt and not target:get("includedirs")
           and not target:get("defines"), "Unsupported synchronous JVM build options")
    assert(target:values("wros.jvm_main"), "Set the JVM main class with set_wros_jvm_main")
end

function build(target, request, sources)
    local args = {request.mte_flag, "--main-class", target:values("wros.jvm_main"), "-o", target:targetfile()}
    if request.mte_flag == "--legacy-mte" then
        table.join2(args, {"--toolchain", assert(os.getenv("WROS_TOOLCHAIN")), "--sysroots", assert(request.sysroots),
                          "--bundle", assert(os.getenv("WROS_JVM_BUNDLE"))})
    end
    for _, operation in ipairs(request.operations) do
        table.insert(args, "--ros-operation")
        table.insert(args, operation)
    end
    table.join2(args, sources)
    os.vrunv(request.program, args)
end
