-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("booster-common-csharp")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("common")
    set_kind("binary")
    set_language("csharp")
    set_ros_platform("booster")
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_exports("Robot.Start")
    add_wros_operations("abi")
    set_wros_test_queries("abi")
    add_files("Robot.cs")
    add_wros_tests("int", "aot")
target_end()
