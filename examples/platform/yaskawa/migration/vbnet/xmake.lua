-- @file xmake.lua
-- @brief Build the Visual Basic project and interpret ROS 1 action statuses in both VM engines.
set_project("yaskawa-migration-vbnet")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("goalstatus")
    set_kind("binary")
    set_language("vbnet")
    set_ros_platform("yaskawa")
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_exports("GoalStatus.Start")
    add_wros_operations("abi")
    add_files("GoalStatus.vb")
    set_wros_test_queries("abi")
    add_wros_tests("int", "aot")
target_end()
