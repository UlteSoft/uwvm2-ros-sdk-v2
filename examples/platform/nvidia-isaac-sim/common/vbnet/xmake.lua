-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("nvidia-isaac-sim-common-vbnet")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("common")
    set_kind("binary")
    set_language("vbnet")
    set_ros_platform("nvidia-isaac-sim")
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_exports("Robot.Start")
    add_wros_operations("abi")
    set_wros_test_queries("abi")
    add_files("Robot.vb")
    add_wros_tests("int", "aot")
target_end()
