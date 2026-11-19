-- @file xmake.lua
-- @brief Build a source-level ROS migration example and execute its Wasm assertions.
set_project("wros_migration")
local sdk = os.getenv("UWVM_ROS_SDK_ROOT")
includes(path.join(sdk, "tools/xmake/ros.lua"))

target("action_status")
    set_kind("binary")
    set_language("fsharp")
    set_ros_platform("leju")
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_exports("GoalStatus.Start")
    add_wros_operations("abi")
    set_wros_test_queries("abi")
    add_files("GoalStatus.fs")
    add_wros_tests("int", "aot")
target_end()
