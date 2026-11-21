-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("nvidia-isaac-sim-extension-as")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("extension")
    set_kind("binary")
    set_language("as")
    set_ros_platform("nvidia-isaac-sim")
    set_wros_profile({core = "3.0", eh = false, mte = true})
    set_symbols("debug")
    add_wros_operations("capability.open", "driver.connect", "capability.close")
    set_wros_test_policy("platform-driver-denial")
    add_files("driver.ts")
    add_wros_tests("int", "aot")
target_end()
