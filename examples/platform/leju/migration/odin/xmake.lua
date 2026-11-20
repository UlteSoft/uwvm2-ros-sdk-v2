-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("leju-migration-odin")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("migration")
    set_kind("binary")
    set_language("odin")
    set_ros_platform("leju")
    set_wros_profile({core = "3.0", eh = false, mte = true})
    set_symbols("debug")
    add_files("grid.odin")
    add_wros_tests("int", "aot")
target_end()
