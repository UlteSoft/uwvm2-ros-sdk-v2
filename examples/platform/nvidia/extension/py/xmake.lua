-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("nvidia-extension-py")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("extension")
    set_kind("binary")
    set_language("py")
    set_ros_platform("nvidia")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_operations("capability.open", "driver.connect", "capability.close")
    set_wros_test_queries("realtime-clock", "monotonic-clock", "realtime-resolution", "monotonic-resolution")
    set_wros_test_policy("platform-driver-denial")
    add_files("body.py")
    add_wros_tests("int", "aot")
target_end()
