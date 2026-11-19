-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("ufactory-common-fortran")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("common")
    set_kind("binary")
    set_language("fortran")
    set_ros_platform("ufactory")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_optimize("fastest")
    set_symbols("debug")
    set_wros_test_queries("abi")
    add_files("body.f90")
    add_wros_tests("int", "aot")
target_end()
