set_project("wasip1-external-c")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("external-c")
    set_kind("binary")
    set_language("c")
    set_wros_profile({
        std = "c17", abi = "wasm32", core = "3.0", eh = false,
        mte = false, memory64 = false, threads = false
    })
    add_files("main.c", "operations.c")
    set_wros_test_queries("realtime-clock")
    add_wros_tests("int", "aot")
target_end()
