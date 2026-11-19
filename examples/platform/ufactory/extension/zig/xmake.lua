-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("ufactory-extension-zig")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("extension")
    set_kind("binary")
    set_language("zig")
    set_ros_platform("ufactory")
    set_wros_profile({core = "3.0", eh = false, mte = true})
    set_wros_test_policy("platform-driver-denial")
    add_files("body.zig")
    add_wros_tests("int", "aot")
target_end()
