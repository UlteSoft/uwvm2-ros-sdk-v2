-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("leju-extension-objectc")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("extension")
    set_kind("binary")
    set_language("objectc")
    set_ros_platform("leju")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_optimize("fastest")
    set_symbols("debug")
    set_wros_test_policy("platform-driver-denial")
    add_files("driver.m")
    add_wros_tests("int", "aot")
target_end()
