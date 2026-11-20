-- @file xmake.lua
-- @brief Build a source-level ROS migration example and execute its Wasm assertions.
set_project("wros_migration")
local sdk = os.getenv("UWVM_ROS_SDK_ROOT")
includes(path.join(sdk, "tools/xmake/ros.lua"))

local source = path.join(sdk, "examples/shared/migration/c")
local generated = path.join(os.projectdir(), "build", "wros-resource")
local locks = {
    ["5.0"] = path.join(os.scriptdir(), "upstream.lock"),
    ["5.1"] = path.join(os.scriptdir(), "upstream-5.1.lock")
}
option("isaac_ros_release")
    set_default("5.0")
    set_showmenu(true)
    set_values("5.0", "5.1")
    set_description("Isaac ROS release for the local tensor definition")
option_end()

target("resource")
    set_kind("binary")
    set_language("c")
    set_ros_platform("nvidia-isaac-ros")
    set_optimize("fastest")
    set_symbols("debug")
    set_wros_profile({std = "c23"})
    add_includedirs(generated)
    add_files("resource.c")
    before_build(function ()
        local release = get_config("isaac_ros_release")
        local lock = assert(locks[release], "Unsupported Isaac ROS release: " .. tostring(release))
        local args = {"-I", "-B", path.join(source, "prepare.py"), "--platform-lock", lock, "--output", generated}
        local package = os.getenv("WROS_ROS_PACKAGE_ROOT")
        if package then
            table.insert(args, "--package-root")
            table.insert(args, package)
        end
        os.vrunv("python3", args)
    end)
    add_wros_tests("int", "aot")
target_end()
