set_project("robot_filter")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

local function fortran_profile()
    set_language("fortran")
    set_ros_platform(os.getenv("WROS_PLATFORM") or "unitree")
    set_wros_profile({core = "3.0", mte = true, eh = true})
    set_optimize("fastest")
    set_symbols("debug")
end

target("sample_filter")
    set_kind("static")
    fortran_profile()
    add_files("kernel.f90")
target_end()

target("robot")
    set_kind("binary")
    fortran_profile()
    add_files("body.f90")
    add_deps("sample_filter")
target_end()
