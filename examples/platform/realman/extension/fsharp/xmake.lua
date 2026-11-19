-- @file xmake.lua
-- @brief Build the F# project and check both driver permission gates in both VM engines.
set_project("realman-extension-fsharp")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("driver")
    set_kind("binary")
    set_language("fsharp")
    set_ros_platform("realman")
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_exports("Driver.Start")
    add_wros_operations("driver.connect")
    add_files("Driver.fs")
    set_wros_test_policy("platform-driver-denial")
    add_wros_tests("int", "aot")
target_end()
