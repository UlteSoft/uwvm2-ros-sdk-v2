-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("agilex-common-wat")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("common")
    set_kind("binary")
    set_language("wat")
    set_ros_platform("agilex")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_symbols("debug")
    add_wros_operations("abi")
    set_wros_test_queries("abi")
    add_files("controller.wat")
    add_wros_tests("int", "aot")
target_end()
