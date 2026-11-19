-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("nvidia-groot-migration-go")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("migration")
    set_kind("binary")
    set_language("go")
    set_ros_platform("nvidia-groot")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    add_files("controller.go")
    add_wros_tests("int", "aot")
target_end()
