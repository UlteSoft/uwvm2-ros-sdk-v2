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
    set_extensions(".c", ".cc", ".cpp", ".cxx", ".C", ".lua", ".go", ".mod", ".f", ".F", ".f90", ".F90", ".f95", ".f03", ".f08", ".f18", ".for", ".ftn",
                   ".rs", ".java", ".kt", ".cs", ".ts", ".nim", ".m", ".d", ".o", ".a")
rule_end()

rule("wros.application")
    on_load(function (target)
        import("dispatch", {rootdir = path.join(sdk, "tools/xmake"), anonymous = true}).configure(target, sdk)
    end)
    on_build(function (target)
        import("dispatch", {rootdir = path.join(sdk, "tools/xmake"), anonymous = true}).build(target)
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
        if key == "core" or key == "eh" or key == "mte" or key == "std" or key == "lua_abi" or key == "lua_seed" or key == "build_receipt" then
            set_values("wros." .. key, tostring(value))
        else
            set_values("wros.unknown", tostring(key))
        end
    end
end

function add_wros_exports(...)
    add_values("wros.exports", ...)
end

function add_wros_lua_operations(...)
    add_values("wros.lua_operations", ...)
end

function set_wros_jvm_main(class_name)
    set_values("wros.jvm_main", class_name)
end
