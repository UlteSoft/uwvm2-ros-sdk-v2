-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("leju-migration-rs")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("migration")
    set_kind("binary")
    set_language("rs")
    set_ros_platform("leju")
    set_wros_profile({core = "3.0", eh = false, mte = true})
    add_files("grid.rs")
    add_wros_tests("int", "aot")
target_end()
