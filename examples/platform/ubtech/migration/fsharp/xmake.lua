-- @file xmake.lua
-- @brief Build a source-level ROS migration example and execute its Wasm assertions.
set_project("wros_migration")
local sdk = assert(os.getenv("UWVM_ROS_SDK_ROOT"), "Select an installed SDK")
includes(path.join(sdk, "tools/xmake/ros.lua"))

target("action_status")
    set_kind("binary")
    set_language("fsharp")
    set_ros_platform("ubtech")
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_exports("GoalStatus.Start")
    add_wros_operations("abi")
    add_files(path.join(sdk, "examples/shared/migration/fsharp/GoalStatus.fs"))
    add_wros_tests("int", "aot")
target_end()
