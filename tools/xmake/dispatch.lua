-- Build with the selected Wasm frontend. Configuration only reads SDK descriptors.
local function identifier(value)
    return type(value) == "string" and value:match("^[a-z][a-z0-9_%-]*$")
end

local function contains(values, search)
    for _, value in ipairs(values) do
        if value == search then return true end
    end
    return false
end

local function selection(root)
    local variant = path.filename(root)
    local langdir = path.directory(root)
    local language = path.filename(langdir)
    local components = {java = "synchronous-aot", kotlin = "synchronous-aot", csharp = "numeric-aot", vbnet = "numeric-aot", fsharp = "numeric-aot"}
    local expected = components[language]
    if expected then
        local migration = variant == "migration" and (language == "csharp" or language == "vbnet" or language == "fsharp")
        assert(variant == expected or variant == "development" or migration, "Select the installed " .. expected .. " component for " .. language)
    else
        local migration = variant == "migration" and (language == "c" or language == "cpp")
        assert(variant == "development" or variant == "compiler-source" or migration, "Select an installed Wasm development directory")
    end
    local platdir = path.directory(langdir)
    local commit = path.filename(path.directory(platdir))
    assert(#commit == 40 and commit:match("^[0-9a-f]+$"), "Select an immutable SDK installation")
    return commit, path.filename(platdir), language
end

local function provider(directory, name)
    assert(os.isfile(path.join(directory, name .. ".lua")), "Missing installed adapter: " .. directory)
    return import(name, {rootdir = directory, anonymous = true, nocache = true})
end

local function boolean(target, key, default)
    local value = target:values("wros." .. key)
    if value == nil then return default end
    assert(value == "true" or value == "false", key .. " expects true or false")
    return value == "true"
end

function configure(target, entry)
    local root = path.absolute(target:values("wros.selection") or entry)
    local commit, platform, language = selection(root)
    assert(commit == selection(entry), "SDK selections belong to different commits")
    local requested_platform = target:values("wros.platform")
    local requested_language = target:values("wros.language")
    assert(identifier(requested_platform) and requested_platform == platform, "Platform is not installed in this selection: " .. tostring(requested_platform))
    assert(identifier(requested_language) and requested_language == language, "Language is not installed in this selection: " .. tostring(requested_language))
    local platform_info = provider(path.join(root, "platform", platform, "xmake"), "platform").describe()
    assert(platform_info.id == platform, "Installed platform descriptor does not match this selection")
    local implementation = provider(path.join(root, "language", language, "xmake"), "adapter")
    local adapter = implementation.describe()
    assert(adapter.id == language and identifier(adapter.program), "Invalid installed language adapter")
    local program = path.join(root, "bin", adapter.program)
    assert(os.isfile(program), "Missing installed compiler frontend: " .. program)
    assert(not target:values("wros.unknown"), "Unknown WROS profile field: " .. tostring(target:values("wros.unknown")))
    assert(not target:values("wros.jvm_main") or language == "java" or language == "kotlin", "set_wros_jvm_main requires a JVM language")
    local core = target:values("wros.core") or "3.0"
    assert(core == "3.0" or core == "mvp", "core expects 3.0 or mvp")
    local eh = boolean(target, "eh", core ~= "mvp" and language ~= "rs")
    assert(target:values("wros.herbceptions") == nil or language == "cpp",
           "herbceptions is a C++ profile option")
    local legacy_mte = target:values("wros.mte") == "legacy"
    local mte = legacy_mte or boolean(target, "mte", true)
    local mte_flag = legacy_mte and "--legacy-mte" or (mte and "--mte" or "--no-mte")
    local sysroots = (not mte and os.getenv("WROS_SYSROOTS_NO_MTE")) or os.getenv("WROS_SYSROOTS")
    local arch = target:arch()
    local plat = target:plat()
    assert(plat == "wasm-wasip1" or plat == "wasm-wasip1-threads", "Unsupported Wasm target platform")
    assert(arch == "wasm32" or arch == "wasm64", "Unsupported Wasm address width")
    local threads = plat == "wasm-wasip1-threads"
    assert(core ~= "mvp" or (arch == "wasm32" and not eh and not threads), "MVP requires wasm32, no threads and no EH")
    local kind = target:kind()
    assert(kind == "binary" or (kind == "static" and (adapter.family == "c" or adapter.static == true)), "Unsupported artifact kind: " .. tostring(kind))
    local build_receipt = boolean(target, "build_receipt", false)
    assert(not build_receipt or kind == "binary", "Deployment build receipts require a linked Wasm binary")
    local exports = table.wrap(target:values("wros.exports"))
    local operations = table.wrap(target:values("wros.operations"))
    assert(language == "lua" or language == "js" or language == "java" or language == "kotlin" or language == "csharp" or language == "vbnet" or language == "fsharp" or #operations == 0,
           "add_wros_operations requires a target with selectable ROS imports")
    local lua_operations = table.wrap(target:values("wros.lua_operations"))
    assert(language == "lua" or #lua_operations == 0, "add_wros_lua_operations requires a Lua target")
    local lua_abi = boolean(target, "lua_abi", false)
    if language == "lua" then table.join2(lua_operations, operations) end
    local lua_seed = target:values("wros.lua_seed")
    if lua_seed then
        assert(language == "lua" and lua_seed:match("^%d+$") and tonumber(lua_seed) <= 4294967295,
               "lua_seed expects an unsigned decimal 32-bit seed on a Lua target")
    end
    local std = target:values("wros.std")
    assert(language == "lua" or not lua_abi, "lua_abi is specific to Lua")
    for _, key in ipairs({"links", "syslinks", "linkdirs", "cxflags", "cflags", "cxxflags", "ldflags", "shflags", "frameworks", "packages"}) do
        local setting = target:get(key)
        -- Xmake's rust.build load hook adds this flag to binary targets.
        -- wrrs selects its own crate type and never forwards these flags.
        local rust_binary = language == "rs" and key == "ldflags" and table.wrap(setting) or {}
        assert(not setting or (#rust_binary == 1 and rust_binary[1] == "--crate-type=bin"),
               "Unsupported guest target setting: " .. key)
    end
    local name = target:get("filename") or (target:name() .. (kind == "binary" and ".wasm" or ".a"))
    local extension = kind == "binary" and ".wasm" or ".a"
    assert(path.extension(name) == extension, "Target filename must end in " .. extension)
    target:set("filename", name)
    local request = {root = root, adapter = adapter, program = program, kind = kind, arch = arch, build_receipt = build_receipt,
        core = core, eh = eh, mte = mte, mte_flag = mte_flag, sysroots = sysroots, threads = threads, exports = exports, lua_abi = lua_abi, lua_seed = lua_seed, lua_operations = lua_operations, operations = operations, std = std, implementation = implementation}
    if implementation.validate then implementation.validate(target, request) end
    target:data_set("wros.request", request)
end

local function qualified_inputs(target, request)
    local sources = target:sourcefiles()
    assert(#sources > 0, "WROS target needs source files")
    for _, file in ipairs(sources) do
        assert(contains(request.adapter.extensions, path.extension(file)), "Unsupported source for " .. request.adapter.id .. ": " .. file)
        assert(os.isfile(file), "Missing source: " .. file)
    end
    return sources
end

local function compiler_args(target, request)
    local args = table.join({"--target", request.arch}, request.tool_args)
    local optimize = target:get("optimize")
    local symbols = table.wrap(target:get("symbols"))
    table.join2(args, {"--core", request.core, request.eh and "--eh" or "--no-eh", request.mte_flag})
    if request.threads then table.insert(args, "-pthread") end
    if request.std then table.join2(args, {"--std", request.std}) end
    if request.adapter.id == "cpp" then
        table.insert(args, boolean(target, "herbceptions", true) and "--herbceptions" or "--no-herbceptions")
    end
    local levels = {none = "0", fast = "1", faster = "2", fastest = "3", smallest = "s"}
    if optimize or not request.site then
        table.insert(args, "-O" .. assert(levels[optimize or "faster"], "Unsupported guest optimization"))
    end
    for _, value in ipairs(symbols) do
        assert(value == "debug", "Unsupported guest symbols setting: " .. value)
        table.insert(args, "-g")
    end
    for _, dir in ipairs(table.wrap(target:get("includedirs"))) do table.join2(args, {"-I", dir}) end
    for _, define in ipairs(table.wrap(target:get("defines"))) do table.join2(args, {"-D", define}) end
    return args
end

function build(target)
    local request = assert(target:data("wros.request"))
    local sources = qualified_inputs(target, request)
    local output = target:targetfile()
    os.mkdir(path.directory(output))
    if request.adapter.family == "c" or request.adapter.id == "fortran" or request.adapter.id == "lua" or request.adapter.id == "js" or request.adapter.id == "nim" then
        local toolchain = os.getenv("WROS_TOOLCHAIN")
        request.site = not toolchain and not request.sysroots and
                       os.isfile(path.join(request.root, "share/qualification/site-profile.json"))
        if request.site then
            assert(request.mte_flag == "--mte", "Provide explicit matching tools and sysroots for another MTE mode")
            request.tool_args = {}
        else
            assert(toolchain and request.sysroots, "Provide a site installation or both WROS_TOOLCHAIN and WROS_SYSROOTS")
            request.tool_args = {"--toolchain", toolchain, "--sysroots", request.sysroots}
        end
    end
    if request.implementation.build then
        request.implementation.build(target, request, sources)
        return
    end
    local args = compiler_args(target, request)
    if request.kind == "static" then
        assert(#request.exports == 0 and #target:orderdeps() == 0, "A static producer accepts sources only")
        local objects = {}
        for index, file in ipairs(sources) do
            assert(path.extension(file) ~= ".a" and path.extension(file) ~= ".o", "A static producer expects source files")
            local object = path.join(target:autogendir(), "wros", index .. ".o")
            os.mkdir(path.directory(object))
            os.vrunv(request.program, table.join(args, {"-c", file, "-o", object}))
            table.insert(objects, object)
        end
        if request.site then
            os.vrunv("python3", table.join({"-I", "-B", path.join(request.root, "tools/xmake/site_archive.py"),
                                          request.adapter.id, "-o", output}, objects))
        else
            os.vrunv(path.join(request.root, "bin/wrar"), table.join({"--toolchain", os.getenv("WROS_TOOLCHAIN"), "-o", output}, objects))
        end
        return
    end
    if request.build_receipt then table.insert(args, "--build-receipt") end
    table.join2(args, {"--reactor", "--export", "_start"})
    for _, name in ipairs(request.exports) do table.join2(args, {"--export", name}) end
    table.join2(args, sources)
    for _, dep in ipairs(target:orderdeps()) do
        local other = dep:data("wros.request")
        assert(other and other.kind == "static", "Dependency must be an installed WROS static producer")
        table.insert(args, dep:targetfile())
    end
    os.vrunv(request.program, table.join(args, {"-o", output}))
end
