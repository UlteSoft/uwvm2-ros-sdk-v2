-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("booster-extension-rs")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("extension")
    set_kind("binary")
    set_language("rs")
    set_ros_platform("booster")
    set_wros_profile({core = "3.0", eh = false, mte = true})
    set_wros_test_policy("platform-driver-denial")
    add_files("driver.rs")
    add_wros_tests("int", "aot")
target_end()
