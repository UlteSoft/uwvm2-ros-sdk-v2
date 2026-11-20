-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("kuka-migration-as")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("migration")
    set_kind("binary")
    set_language("as")
    set_ros_platform("kuka")
    set_wros_profile({core = "3.0", eh = false, mte = true})
    set_symbols("debug")
    add_files("grid.ts")
    add_wros_tests("int", "aot")
target_end()
