-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("nvidia-groot-common-tinygo")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("common")
    set_kind("binary")
    set_language("tinygo")
    set_ros_platform("nvidia-groot")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_optimize("fastest")
    set_symbols("debug")
    set_wros_test_queries("abi")
    add_files("go.mod")
    add_wros_tests("int", "aot")
target_end()
