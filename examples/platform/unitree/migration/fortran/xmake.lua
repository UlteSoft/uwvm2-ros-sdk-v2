-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("unitree-migration-fortran")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("migration")
    set_kind("binary")
    set_language("fortran")
    set_ros_platform("unitree")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_optimize("fastest")
    set_symbols("debug")
    add_files("grid.f90")
    add_wros_tests("int", "aot")
target_end()
