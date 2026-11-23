# WebAssembly text projects

Install `--language wat`. Copy `examples/wat`, configure the environment in the [installation guide](../install-xmake.md), then run `xmake build` and `xmake test -j1`. The project declares its `uwvm_ros_v2.abi` import explicitly and checks the return value at runtime.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrwat" main.wat --target wasm32 --core 3.0 \
    --mte --eh --ros-operation abi -o guest.wasm
```

`--ros-operation` declares one import per occurrence. Its signature must match the installed contract. WAT describes memory widths in the module. For this assembler, `--target wasm64` enables memory64 validation and `--target wasm32` disables it. Use `-g` for names and DWARF information and `--build-receipt` for the compiler's build record. In a source installation, the editable crate, lockfile, vendored dependencies and rebuild script are under `src/compilers/wrwat`.

`include/u2rosv2/universal/wat/uwrosv2` contains 38 domain modules and an aggregate `scene.wat`. Copy each required import into your own module so that the VM sees the calling guest and its memory. The comments beside each import describe the operation, caller authority, named parameters, record layout, memory lifetimes and status-dependent output. For a dedicated platform, the decoder module is under `include/u2rosv2/platform/<platform>/wat`. Its runnable example is at `examples/<platform>/wat`.
