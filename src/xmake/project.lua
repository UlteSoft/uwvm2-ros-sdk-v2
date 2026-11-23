local function value(target, key)
    return target:values("wros." .. key)
end

local function boolean(target, key, default)
    local item = value(target, key)
    if item == nil then return default end
    assert(item == "true" or item == "false", key .. " expects a boolean")
    return item == "true"
end

function configure(target, sdk)
    local json = import("core.base.json")
    local selected = json.loadfile(path.join(sdk, "selection.json"))
    local lang = value(target, "language")
    if lang == "c++" then lang = "cpp" end
    if lang == "rs" then lang = "rust" end
    if lang == "wrwat" then lang = "wat" end
    if lang == "assemblyscript" then lang = "as" end
    if lang == "javascript" then lang = "js" end
    if lang == "ts" then lang = "typescript" end
    if lang == "python" then lang = "py" end
    local cfamily = lang == "c" or lang == "cpp" or lang == "objc" or lang == "objcpp"
    local ecmascript = lang == "js" or lang == "typescript"
    assert(selected.language == lang, "requested language differs from the installed selection")
    assert(not value(target, "platform") or value(target, "platform") == selected.platform, "requested platform is not installed")
    assert(not value(target, "unknown"), "unknown WROS option: " .. tostring(value(target, "unknown")))
    assert(target:kind() == "binary", "this guest rule builds executable Wasm modules")
    local core = value(target, "core") or "3.0"
    assert(core == "3.0" or core == "mvp", "core must be 3.0 or mvp")
    local abi = value(target, "abi") or target:arch()
    assert(abi == "wasm32" or abi == "wasm64", "abi must be wasm32 or wasm64")
    local memory64 = boolean(target, "memory64", core == "3.0")
    local rust_bindings = lang == "rust" and selected.mode == "bindings"
    local eh = boolean(target, "eh", core == "3.0" and not rust_bindings and lang ~= "as")
    local mte = boolean(target, "mte", not rust_bindings)
    local threaded_platform = target:plat() == "wasm-wasip1-threads"
    local threads = boolean(target, "threads", threaded_platform)
    assert(not threaded_platform or threads, "the threaded Xmake platform requires threads")
    assert(core ~= "mvp" or not (memory64 or eh or threads), "MVP requires memory64, EH and threads disabled")
    if rust_bindings then
        assert(abi == "wasm32" and core == "3.0" and not (eh or mte or threads),
               "upstream Rust bindings support wasm32, Core 3, panic=abort, no MTE and no threads")
    end
    assert(not value(target, "herbceptions") or lang == "cpp", "herbceptions applies to C++")
    assert(not value(target, "std") or cfamily, "std applies to C-family languages")
    assert(not value(target, "as_driver") or lang == "as", "as_driver selects AssemblyScript bounded staging")
    assert(not value(target, "entry") or ecmascript or lang == "py", "set_wros_entry selects a JavaScript, TypeScript or Python entry")
    if lang == "java" then
        assert(value(target, "main_class"), "set_wros_main_class requires the binary name of the Java entry")
        assert(abi == "wasm32" and core == "3.0" and eh and mte and memory64 and not threads,
               "Java requires wasm32, Core 3.0, memory64 enabled, EH, MTE and no threads")
    else
        assert(not value(target, "main_class"), "set_wros_main_class applies to Java")
    end
    local operations = table.wrap(value(target, "operations"))
    assert(#operations == 0 or lang == "wat" or lang == "as" or ecmascript or lang == "py",
           "add_wros_operations selects imports for WAT, AssemblyScript, JavaScript, TypeScript and Python")
    local exports = table.wrap(value(target, "exports"))
    assert(#exports == 0 or cfamily, "C-family frontends accept additional link exports")
    local libraries = table.wrap(target:get("links"))
    assert(#libraries == 0 or cfamily, "add_links selects bundled C-family sysroot libraries")
    local queries = table.wrap(value(target, "queries"))
    for _, query in ipairs(queries) do
        assert(query == "abi" or query == "realtime-clock" or (query == "python-runtime" and lang == "py")
               or (query == "go-runtime" and (lang == "go" or lang == "tinygo")), "unknown local test query: " .. tostring(query))
    end
    for _, setting in ipairs({"syslinks", "linkdirs", "cxflags", "cflags", "cxxflags", "ldflags",
                               "shflags", "frameworks", "packages"}) do
        local items = table.wrap(target:get(setting))
        local rust_internal = lang == "rust" and setting == "ldflags" and #items == 1 and items[1] == "--crate-type=bin"
        assert(#items == 0 or rust_internal, "unsupported guest target setting: " .. setting)
    end
    local output = target:get("filename") or target:name() .. ".wasm"
    assert(path.extension(output) == ".wasm", "guest filename must end in .wasm")
    target:set("filename", output)
    target:data_set("wros.request", {sdk = sdk, lang = lang, platform = selected.platform, abi = abi,
        core = core, memory64 = memory64, threads = threads, eh = eh, mte = mte, exports = exports, libraries = libraries,
        main_class = value(target, "main_class"), entry = value(target, "entry"), as_driver = boolean(target, "as_driver", false),
        operations = operations, queries = queries, std = value(target, "std"), herbceptions = boolean(target, "herbceptions", true)})
end

function build(target)
    local req = assert(target:data("wros.request"))
    local output = path.absolute(target:targetfile())
    os.mkdir(path.directory(output))
    local files = target:sourcefiles()
    assert(#files > 0 and #target:orderdeps() == 0, "declare source files directly for this Wasm application")
    local args = {"-I", "-B", path.join(req.sdk, "tools/xmake/build_guest.py"), "--sdk", req.sdk,
        "--language", req.lang, "--platform", req.platform, "--abi", req.abi, "--core", req.core, "-o", output,
        req.mte and "--mte" or "--no-mte", req.eh and "--eh" or "--no-eh",
        req.memory64 and "--memory64" or "--no-memory64", req.threads and "--threads" or "--no-threads"}
    if req.lang == "cpp" then table.insert(args, req.herbceptions and "--herbceptions" or "--no-herbceptions") end
    if req.as_driver then table.insert(args, "--as-driver") end
    if req.lang == "py" then table.join2(args, {"--project-root", path.absolute(target:scriptdir())}) end
    if req.entry then table.join2(args, {"--entry", path.absolute(req.entry, target:scriptdir())}) end
    if req.main_class then table.join2(args, {"--main-class", req.main_class}) end
    if req.std then table.join2(args, {"--std", req.std}) end
    local optimize = target:get("optimize")
    if optimize then
        local levels = {none = "0", fast = "1", faster = "2", fastest = "3", smallest = "s"}
        table.join2(args, {"-O", assert(levels[optimize], "unsupported optimization")})
    end
    for _, sym in ipairs(table.wrap(target:get("symbols"))) do
        assert(sym == "debug", "unsupported debug option")
        table.insert(args, "-g")
    end
    for _, name in ipairs(req.operations) do table.join2(args, {"--operation", name}) end
    for _, name in ipairs(req.libraries) do table.join2(args, {"--link-library", name}) end
    for _, name in ipairs(req.exports) do table.join2(args, {"--export", name}) end
    for _, dir in ipairs(table.wrap(target:get("includedirs"))) do table.join2(args, {"-I", path.absolute(dir)}) end
    for _, def in ipairs(table.wrap(target:get("defines"))) do table.join2(args, {"-D", def}) end
    table.insert(args, "--")
    for _, file in ipairs(files) do table.insert(args, path.absolute(file)) end
    os.vrunv("python3", args)
end

function run(target, engine, istest)
    assert(engine == "int" or engine == "aot", "select int or aot for a guest execution test")
    local req = assert(target:data("wros.request"))
    local args = {"-I", "-B", path.join(req.sdk, "tools/xmake/run_guest.py"), path.absolute(target:targetfile()),
        "--engine", engine, "--core", req.core, req.mte and "--mte" or "--no-mte", req.eh and "--eh" or "--no-eh",
        req.memory64 and "--memory64" or "--no-memory64", req.threads and "--threads" or "--no-threads"}
    for _, query in ipairs(req.queries) do table.join2(args, {"--query", query}) end
    if istest then
        return os.execv("python3", args, {try = true}) == 0
    end
    os.execv("python3", args)
end
