-- @file xmake.lua
-- @brief Build and test this platform's guest modules.
set_project("kinova-migration-java")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("migration")
    set_kind("binary")
    set_language("java")
    set_ros_platform("kinova")
    set_wros_profile({core = "3.0", eh = true, mte = true})
    set_optimize("fastest")
    set_symbols("debug")
    set_wros_jvm_main("example.Main")
    add_files("Main.java")
    add_wros_tests("int", "aot")
target_end()
