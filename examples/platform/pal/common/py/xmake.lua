-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("pal-common-py")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("common")
    set_kind("binary")
    set_language("py")
    set_ros_platform("pal")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_operations("abi")
    set_wros_test_queries("abi", "realtime-clock", "monotonic-clock", "realtime-resolution", "monotonic-resolution")
    add_files("body.py")
    add_wros_tests("int", "aot")
target_end()
