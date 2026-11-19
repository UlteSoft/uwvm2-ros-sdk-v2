-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("kinova-extension-tinygo")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("extension")
    set_kind("binary")
    set_language("tinygo")
    set_ros_platform("kinova")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_optimize("fastest")
    set_symbols("debug")
    set_wros_test_policy("platform-driver-denial")
    add_files("go.mod")
    add_wros_tests("int", "aot")
target_end()
