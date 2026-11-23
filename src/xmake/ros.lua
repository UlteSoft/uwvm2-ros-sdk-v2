-- Include this file from a guest project's xmake.lua.
local sdk = path.directory(path.directory(path.absolute(os.scriptdir())))
set_defaultplat("wasm-wasip1")
set_defaultarchs("wasm32")
set_allowedplats("wasm-wasip1", "wasm-wasip1-threads")
set_allowedarchs("wasm32", "wasm64")

toolchain("uwrosv2.guest")
    set_kind("standalone")
    on_check(function () return true end)
toolchain_end()

rule("uwrosv2.source")
    set_extensions(".c", ".cc", ".cpp", ".cxx", ".m", ".mm", ".rs", ".wat", ".ts", ".js", ".mjs", ".mod", ".py", ".java")
rule_end()

rule("uwrosv2.application")
    on_load(function (target)
        import("project", {rootdir = path.join(sdk, "tools/xmake"), anonymous = true}).configure(target, sdk)
    end)
    on_build(function (target)
        import("project", {rootdir = path.join(sdk, "tools/xmake"), anonymous = true}).build(target)
    end)
    on_run(function (target)
        import("core.base.option")
        assert(not option.get("arguments") and not target:get("runargs"), "guest arguments require a deployment")
        import("project", {rootdir = path.join(sdk, "tools/xmake"), anonymous = true}).run(target, "int")
    end)
    on_test(function (target, opt)
        local engine = opt.name:match("/([^/]+)$") or opt.name
        return import("project", {rootdir = path.join(sdk, "tools/xmake"), anonymous = true}).run(target, engine, true)
    end)
rule_end()

function set_language(name)
    set_values("wros.language", name)
    set_toolchains("uwrosv2.guest")
    add_rules("uwrosv2.source", {override = true})
    add_rules("uwrosv2.application")
end

function set_ros_platform(name)
    set_values("wros.platform", name)
end

function set_wros_entry(filename)
    set_values("wros.entry", filename)
end

function set_wros_main_class(name)
    set_values("wros.main_class", name)
end

function set_wros_profile(profile)
    for name, value in pairs(profile) do
        if name == "abi" or name == "core" or name == "memory64" or name == "eh" or name == "threads"
            or name == "mte" or name == "herbceptions" or name == "std" or name == "as_driver" then
            set_values("wros." .. name, tostring(value))
        else
            set_values("wros.unknown", name)
        end
    end
end

function add_wros_operations(...)
    add_values("wros.operations", ...)
end

function add_wros_exports(...)
    add_values("wros.exports", ...)
end

function set_wros_test_queries(...)
    set_values("wros.queries", ...)
end

function add_wros_tests(...)
    for _, engine in ipairs({...}) do
        if engine == "int" or engine == "aot" then
            add_tests(engine)
        else
            set_values("wros.unknown", "test engine " .. tostring(engine))
        end
    end
end
