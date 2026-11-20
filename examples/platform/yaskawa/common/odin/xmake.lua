-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("yaskawa-common-odin")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("common")
    set_kind("binary")
    set_language("odin")
    set_ros_platform("yaskawa")
    set_wros_profile({core = "3.0", eh = false, mte = true})
    set_symbols("debug")
    add_wros_operations("abi")
    set_wros_test_queries("abi")
    add_files("controller.odin")
    add_wros_tests("int", "aot")
target_end()
