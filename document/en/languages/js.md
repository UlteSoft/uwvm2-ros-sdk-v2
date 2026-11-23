# JavaScript guests

Install `--language js` and copy `examples/js` to a writable project. The installed `bin/wrjs` uses a private wasm32 C backend to compile the adapted QuickJS interpreter and bundle your modules into a Core Wasm guest. The binary selection includes the runtime and toolchain inputs this build consumes.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrjs" main.mjs --ros-operation abi -o guest.wasm
xmake build
xmake test -j1
```

Import functions such as `wr_abi` from `uwrosv2/capability`. Pass one `--ros-operation` per required host operation, or use `add_wros_operations` in Xmake. The guest represents i64 operands as `bigint`. For a raw address, retain its backing `ArrayBuffer` and obtain the tagged address using `addressOf` from `uwrosv2/memory`. QuickJS uses the WASIp1 real-time clock. The example explicitly requests `"realtime-clock"` in its local test configuration.

Copy `examples/<platform>/js` to run the selected platform's offline decoder. For example, the ABB guest imports `uwrosv2/platform/abb/observation` and passes it a `Uint8Array`. Its Xmake project builds without selecting a ROS host operation. Additional project modules can be passed as `--module sub/math.mjs=path/to/math.mjs` and imported by their relative virtual names. With Xmake, declare the files with `add_files` and choose the application module with `set_wros_entry`. [Installation and Xmake](../install-xmake.md)
