# WebAssembly text

[中文](../zh/wat.md)

`wrwat` assembles and validates core Wasm on a Linux x86-64 build host. The SDK tool builds on wasm-tools 1.263.0 and the pinned WasmMTE validator, with the VM's packed linear-memory instruction encodings. The installer verifies the exact compiler archive. The optional `-- --component compiler-source` selection includes the locked inputs and offline rebuild script. [Upstream release](https://github.com/bytecodealliance/wasm-tools/releases/tag/v1.263.0)

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

Use `--core mvp` for the MVP instruction set, or `--core 3.0` for the default instruction set. The default target is `wasm32`. Selecting `--target wasm64` enables the 64-bit memory and table encodings. Core 3.0 enables its standard exception handling by default. With `--no-eh`, the validator rejects exception instructions and tags. `--threads` enables shared memory and atomic instructions. A threaded wasm32 source can also import the exact `wasi.thread-spawn(i32) -> i32` ABI when it selects one bounded shared owner with `--shared-memory MODULE FIELD`. The VM still requires explicit I1T permission and an execution profile for that module. Preview1 imports remain outside this assembler's import policy.

MTE syntax is enabled by default. Ordinary memory declarations and instructions remain valid. Express allocation and tag operations explicitly in WAT. For example, `(memtag.claim $heap (i32.const 128) (i32.const 16))` uses the selected memory's width, resolves its index and encodes the packed VM instruction. Both folded instructions and flat stack notation work. The binary validator checks each immediate and operand type. Allocation lifetime and pointer use follow the authored WAT. The validator also checks version 2 static tag registrations in the `uwvm.memtag.linear.globals` custom section.

After a valid managed claim, the VM enforces the nearby allocation color exclusions and chooses among eligible tags. The assembler does not choose tags. `--no-mte` or Xmake `mte = false` permits raw memory and rejects explicit MTE instructions in the build. A module with explicit MTE instructions can independently be run with the VM's `--runtime-disable-memtag` execution policy.

Use `--ros-operation NAME` once per imported operation. Xmake expresses the same selection with `add_wros_operations`. The final ROS import set must match the declaration and the installed ROSv2 signatures exactly. Component binaries and Component Model interface conventions are rejected. Use `-g` or Xmake `set_symbols("debug")` to generate DWARF from WAT, with the original source's basename as the source name. A build receipt records the source, output, assembler digest and selected profile. It can be requested with `--build-receipt` or Xmake `build_receipt = true`.

The installed project at `examples/wat/thread-mte` builds a shared-memory owner and a tagged guest. Set `WROS_PLATFORM` to the installed platform and configure Xmake with `xmake f -p wasm-wasip1-threads -a wasm32`. The project declares the owner with `set_wros_wat_shared_memory("env", "memory")`. The SDK's `tests/wat_thread_mte.py` uses an explicit one-child VM grant and checks the ungranted case separately.

## Shipped projects

Each platform installation includes the following projects under `examples/platform/<platform>`.

- `common/wat` tests a read-only ROSv2 ABI query and fixed-width arithmetic.
- `migration/wat` exercises the unsigned row-major index from ROS Noetic Costmap2D. [Upstream implementation](https://github.com/ros-planning/navigation/blob/f44bb1fc2810399165115cc98b530fe4b9397c18/costmap_2d/include/costmap_2d/costmap_2d.h)
- `extension/wat` uses a private one-page buffer and explicitly disables MTE. The two denial tests check that missing parent or platform permission blocks the connection and leaves the reply buffer untouched. The fixture uses a private socket pair without a robot or vendor driver.
