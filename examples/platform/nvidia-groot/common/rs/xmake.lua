-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("nvidia-groot-common-rs")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("common")
    set_kind("binary")
    set_language("rs")
    set_ros_platform("nvidia-groot")
    set_wros_profile({core = "3.0", eh = false, mte = true})
    set_wros_test_queries("abi")
    add_files("body.rs")
    add_wros_tests("int", "aot")
target_end()
