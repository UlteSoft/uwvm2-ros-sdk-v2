-- @file xmake.lua
-- @brief Build the shared owner and the tagged threaded guest.
set_project("wat-thread-mte")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
set_defaultplat("wasm-wasip1-threads")
local platform = os.getenv("WROS_PLATFORM")

target("owner")
    set_kind("binary")
    set_language("wat")
    set_ros_platform(platform)
    set_wros_profile({core = "3.0"})
    add_files("owner.wat")
target_end()

target("main")
    set_kind("binary")
    set_language("wat")
    set_ros_platform(platform)
    set_wros_profile({core = "3.0", build_receipt = true})
    set_wros_wat_shared_memory("env", "memory")
    set_symbols("debug")
    add_files("main.wat")
target_end()
