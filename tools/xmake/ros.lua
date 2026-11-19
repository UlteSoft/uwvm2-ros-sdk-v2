-- Public SDK declarations. Each target resolves one installed platform and language.
local sdk = path.directory(path.directory(path.absolute(os.scriptdir())))
set_defaultplat("wasm-wasip1")
set_defaultarchs("wasm32")
set_allowedplats("wasm-wasip1", "wasm-wasip1-threads")
set_allowedarchs("wasm32", "wasm64")

toolchain("wros.guest")
    set_kind("standalone")
    on_check(function () return true end)
toolchain_end()

rule("wros.source")
    set_extensions(".c", ".cc", ".cpp", ".cxx", ".C", ".lua", ".js", ".go", ".mod", ".f", ".F", ".f90", ".F90", ".f95", ".f03", ".f08", ".f18", ".for", ".ftn",
                   ".rs", ".java", ".kt", ".cs", ".vb", ".ts", ".nim", ".m", ".d", ".o", ".a")
rule_end()

rule("wros.application")
    on_load(function (target)
        import("dispatch", {rootdir = path.join(sdk, "tools/xmake"), anonymous = true}).configure(target, sdk)
    end)
    on_build(function (target)
        import("dispatch", {rootdir = path.join(sdk, "tools/xmake"), anonymous = true}).build(target)
    end)
    -- @brief Execute the built guest in the exact VM engine requested by add_wros_tests.
    on_test(function (target, opt)
        local engine = opt.name:match("/([^/]+)$") or opt.name
        assert(engine == "int" or engine == "aot", "use add_wros_tests for Wasm execution tests")
        local req = assert(target:data("wros.request"))
        assert(req.kind == "binary", "a VM test requires an executable Wasm target")
        local args = {path.join(req.root, "tools/xmake/run_guest.py"), path.absolute(target:targetfile()),
                      req.arch, req.core, req.threads and "threads" or "single", "--engine", engine,
                      "--exceptions", req.eh and "eh" or "noeh"}
        if req.mte then table.insert(args, "--check-tags") end
        local queries = table.wrap(target:values("wros.test_queries"))
        if #queries > 0 then table.join2(args, {"--queries", table.concat(queries, ",")}) end
        local policy = target:values("wros.test_policy")
        if policy then
            assert(policy == "platform-driver-denial", "unknown WROS test fixture")
            table.join2(args, {"--driver-denial", target:values("wros.platform")})
        end
        local status = os.execv("python3", args, {try = true})
        return status == 0
    end)
    on_run(function (target)
        import("core.base.option")
        assert(not option.get("arguments") and not target:get("runargs"), "Use the deployment VM for guest arguments")
        local request = assert(target:data("wros.request"))
        assert(request.kind == "binary", "Only a Wasm application can run")
        os.execv("python3", {path.join(request.root, "tools/xmake/run_guest.py"),
            path.absolute(target:targetfile()), request.arch, request.core, request.threads and "threads" or "single"})
    end)
rule_end()

local function use_guest_rules()
    set_toolchains("wros.guest")
    add_rules("wros.source", {override = true})
    add_rules("wros.application")
end

function set_language(id)
    set_values("wros.language", id)
    use_guest_rules()
end

function set_ros_platform(id)
    set_values("wros.platform", id)
    use_guest_rules()
end

function set_wros_sdk(directory)
    set_values("wros.selection", directory)
end

function set_wros_profile(profile)
    for key, value in pairs(profile) do
        if key == "core" or key == "eh" or key == "herbceptions" or key == "mte" or key == "std" or key == "lua_abi" or key == "lua_seed" or key == "build_receipt" then
            set_values("wros." .. key, tostring(value))
        else
            set_values("wros.unknown", tostring(key))
        end
    end
end

--- @brief Register real per-engine tests for the current guest binary.
-- Each case executes its own VM process and propagates the guest exit or trap.
function add_wros_tests(...)
    local engines = {...}
    if #engines == 0 then set_values("wros.unknown", "no VM test engine selected") end
    for _, engine in ipairs(engines) do
        if engine == "int" or engine == "aot" then
            add_tests(engine)
        else
            set_values("wros.unknown", "unsupported VM test engine")
        end
    end
end

--- @brief Select the individual read-only VM grants for local guest tests.
function set_wros_test_queries(...)
    set_values("wros.test_queries", ...)
end

--- @brief Select a private socket fixture for testing the platform authorization boundary.
function set_wros_test_policy(policy)
    set_values("wros.test_policy", policy)
end

function add_wros_exports(...)
    add_values("wros.exports", ...)
end

function add_wros_lua_operations(...)
    add_values("wros.lua_operations", ...)
end

function add_wros_operations(...)
    add_values("wros.operations", ...)
end

function set_wros_typescript_entry(file)
    set_values("wros.typescript_entry", file)
end

function set_wros_jvm_main(class_name)
    set_values("wros.jvm_main", class_name)
end
