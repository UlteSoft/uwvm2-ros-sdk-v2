# WebAssembly text

[中文](../zh/wat.md)

`wrwat` assembles WAT directly into core Wasm. The development package contains the official wasm-tools 1.263.0 archive for a Linux x86-64 build host and checks its published SHA-256 before use. The wrapper exposes assembly and validation. [Upstream release](https://github.com/bytecodealliance/wasm-tools/releases/tag/v1.263.0)

## Install and build

Set `REV` to the SDK commit to install and `WROS_VM` to the absolute path of the VM used for the local tests.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language wat --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT=/absolute/path/printed/by/the/installer
cd "$UWVM_ROS_SDK_ROOT/examples/platform/unitree/common/wat"
xmake build
xmake test -j1
"$UWVM_ROS_SDK_ROOT/bin/wrwat" controller.wat --ros-operation abi -g --build-receipt -o controller.wasm
```

Use `--core mvp` for the MVP instruction set, or `--core 3.0` for the default instruction set. The default target is `wasm32`. Selecting `--target wasm64` enables the 64-bit memory and table encodings. Core 3.0 enables its standard exception handling by default. With `--no-eh`, the validator rejects exception instructions and tags. `--threads` on Core 3.0 enables shared memory and atomic instructions. Guest thread creation and WASI imports are outside the assembler's host import policy.

The default MTE setting requires a module without linear memory or data segments. The assembler verifies that condition in the resulting binary. It supports typed stack values, globals, tables and the selected core features. For a module that uses untagged linear memory, pass `--no-mte` or set `mte = false` in the Xmake profile. The assembler does not insert WasmMTE instructions into handwritten memory operations.

Use `--ros-operation NAME` once per imported operation. Xmake expresses the same selection with `add_wros_operations`. The final import set must match the declaration and the installed ROSv2 signatures exactly. This declaration gives the VM no runtime grant. WASI imports, component binaries and Component Model interface conventions are rejected. Use `-g` or Xmake `set_symbols("debug")` to generate DWARF from WAT, with the original source's basename as the source name. A build receipt records the source, output, assembler digest and selected profile. It can be requested with `--build-receipt` or Xmake `build_receipt = true`.

## Shipped projects

Each platform installation includes the following projects under `examples/platform/<platform>`.

- `common/wat` tests a read-only ROSv2 ABI query and fixed-width arithmetic.
- `migration/wat` exercises the unsigned row-major index from ROS Noetic Costmap2D. [Upstream implementation](https://github.com/ros-planning/navigation/blob/f44bb1fc2810399165115cc98b530fe4b9397c18/costmap_2d/include/costmap_2d/costmap_2d.h)
- `extension/wat` uses a private one-page buffer and explicitly disables MTE. The two denial tests check that missing parent or platform permission blocks the connection and leaves the reply buffer untouched. The fixture uses a private socket pair without a robot or vendor driver.
