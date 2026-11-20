-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("deep_robotics-common-as")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("common")
    set_kind("binary")
    set_language("as")
    set_ros_platform("deep_robotics")
    set_wros_profile({core = "3.0", eh = false, mte = true})
    set_symbols("debug")
    add_wros_operations("abi")
    set_wros_test_queries("abi")
    add_files("controller.ts")
    add_wros_tests("int", "aot")
target_end()
