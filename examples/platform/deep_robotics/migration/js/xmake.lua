-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("deep_robotics-migration-js")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("migration")
    set_kind("binary")
    set_language("js")
    set_ros_platform("deep_robotics")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_optimize("fastest")
    set_symbols("debug")
    set_wros_test_queries("realtime-clock")
    add_files("grid.js")
    add_wros_tests("int", "aot")
target_end()
