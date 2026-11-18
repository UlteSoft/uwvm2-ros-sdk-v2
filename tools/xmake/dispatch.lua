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
    assert(variant == "development" or variant == "compiler-source", "Select an installed development or compiler-source directory")
    local langdir = path.directory(root)
    local platdir = path.directory(langdir)
    local commit = path.filename(path.directory(platdir))
    assert(#commit == 40 and commit:match("^[0-9a-f]+$"), "Select an immutable SDK installation")
    return commit, path.filename(platdir), path.filename(langdir)
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
    assert(platform_info.id == platform and contains(platform_info.languages, language), "Platform does not register this language")
    local implementation = provider(path.join(root, "language", language, "xmake"), "adapter")
    local adapter = implementation.describe()
    assert(adapter.id == language and identifier(adapter.program), "Invalid installed language adapter")
    local program = path.join(root, "bin", adapter.program)
    assert(os.isfile(program), "Missing installed compiler frontend: " .. program)
    assert(not target:values("wros.unknown"), "Unknown WROS profile field: " .. tostring(target:values("wros.unknown")))
    local core = target:values("wros.core") or "3.0"
    assert(core == "3.0" or core == "mvp", "core expects 3.0 or mvp")
    local eh = boolean(target, "eh", core ~= "mvp" and language ~= "rs")
    local mte = boolean(target, "mte", true)
    local sysroots = (not mte and os.getenv("WROS_SYSROOTS_NO_MTE")) or os.getenv("WROS_SYSROOTS")
    local arch = target:arch()
    local plat = target:plat()
    assert(plat == "wasm-wasip1" or plat == "wasm-wasip1-threads", "Unsupported Wasm target platform")
    assert(arch == "wasm32" or arch == "wasm64", "Unsupported Wasm address width")
    local threads = plat == "wasm-wasip1-threads"
    assert(core ~= "mvp" or (arch == "wasm32" and not eh and not threads), "MVP requires wasm32, no threads and no EH")
    local kind = target:kind()
    assert(kind == "binary" or (kind == "static" and adapter.family == "c"), "Unsupported artifact kind: " .. tostring(kind))
    local exports = table.wrap(target:values("wros.exports"))
    local lua_abi = boolean(target, "lua_abi", false)
    local std = target:values("wros.std")
    assert(language == "lua" or not lua_abi, "lua_abi is specific to Lua")
    for _, key in ipairs({"links", "syslinks", "linkdirs", "cxflags", "cflags", "cxxflags", "ldflags", "shflags", "frameworks", "packages"}) do
        local setting = target:get(key)
        -- Xmake's rust.build load hook adds this flag to binary targets.
        -- wrrust selects its own crate type and never forwards these flags.
        local rust_binary = language == "rs" and key == "ldflags" and table.wrap(setting) or {}
        assert(not setting or (#rust_binary == 1 and rust_binary[1] == "--crate-type=bin"),
               "Unsupported guest target setting: " .. key)
    end
    local name = target:get("filename") or (target:name() .. (kind == "binary" and ".wasm" or ".a"))
    local extension = kind == "binary" and ".wasm" or ".a"
    assert(path.extension(name) == extension, "Target filename must end in " .. extension)
    target:set("filename", name)
    local request = {root = root, adapter = adapter, program = program, kind = kind, arch = arch,
        core = core, eh = eh, mte = mte, sysroots = sysroots, threads = threads, exports = exports, lua_abi = lua_abi, std = std, implementation = implementation}
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
    local toolchain = assert(os.getenv("WROS_TOOLCHAIN"), "Set WROS_TOOLCHAIN to the Wasm compiler prefix")
    local sysroots = assert(request.sysroots, "Set WROS_SYSROOTS to its matching sysroots.json")
    local args = {"--target", request.arch, "--toolchain", toolchain, "--sysroots", sysroots}
    local optimize = target:get("optimize")
    local symbols = table.wrap(target:get("symbols"))
    table.join2(args, {"--core", request.core, request.eh and "--eh" or "--no-eh", request.mte and "--mte" or "--no-mte"})
    if request.threads then table.insert(args, "-pthread") end
    if request.std then table.join2(args, {"--std", request.std}) end
    local levels = {none = "0", fast = "1", faster = "2", fastest = "3", smallest = "s"}
    table.insert(args, "-O" .. assert(levels[optimize or "faster"], "Unsupported guest optimization"))
    for _, value in ipairs(symbols) do
        assert(value == "debug", "Unsupported guest symbols setting: " .. value)
        table.insert(args, "-g")
    end
    for _, dir in ipairs(table.wrap(target:get("includedirs"))) do table.join2(args, {"-I", dir}) end
    for _, define in ipairs(table.wrap(target:get("defines"))) do table.join2(args, {"-D", define}) end
    return args, toolchain
end

function build(target)
    local request = assert(target:data("wros.request"))
    local sources = qualified_inputs(target, request)
    local output = target:targetfile()
    os.mkdir(path.directory(output))
    if request.implementation.build then
        request.implementation.build(target, request, sources)
        return
    end
    local args, toolchain = compiler_args(target, request)
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
        os.vrunv(path.join(request.root, "bin/wrar"), table.join({"--toolchain", toolchain, "-o", output}, objects))
        return
    end
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
