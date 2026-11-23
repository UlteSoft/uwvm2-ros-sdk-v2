set_project("scoped-guard")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("scoped-guard")
    set_kind("binary")
    set_language("cpp")
    set_wros_profile({std = "c++98"})
    add_files("main.cpp")
target_end()
