# Generic ROS scene

Use this selection for guests that call the `uwvm_ros_v2` scene ABI. `share/abi/ros.json` in the installed SDK records the import names and Wasm signatures. The example at `examples/<language>` asks the VM for its ABI version and traps unless it returns 2. The Xmake project grants the local test the `abi` query. The JavaScript and TypeScript projects also request the WASIp1 real-time clock for QuickJS.
