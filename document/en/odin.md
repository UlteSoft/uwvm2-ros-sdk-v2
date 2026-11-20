# Odin freestanding wasm32

[中文](../zh/odin.md)

`wrodin` builds one freestanding Odin source to core Wasm 3.0. The Linux x86-64 producer was rebuilt with upstream `make release` from the official `dev-2026-11a` monthly source tag. It reports `dev-2026-11:9a69916` and uses the distribution's `libLLVM.so.20.1` runtime. Odin 1.0 GA is outside this release. [Upstream release](https://github.com/odin-lang/Odin/releases/tag/dev-2026-11a) · [Producer inputs](../../third-parties/odin/release.json)

## Install and run

Install the SDK revision and set the absolute paths printed by the installer and provided by your SDK C compiler installation. Select the no-EH wasm32 sysroot receipt for the tagged mode.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language odin --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT=/absolute/path/printed/by/the/installer
export WROS_TOOLCHAIN=/absolute/path/to/paired/sdk/llvm/toolchain
export WROS_SYSROOTS=/absolute/path/to/wasm32/noeh/tagged/sysroots.json
export WROS_VM=/absolute/path/to/uwvm2-ros
cd "$UWVM_ROS_SDK_ROOT/examples/platform/unitree/common/odin"
xmake build
xmake test -j1
```

The common application checks the ROSv2 ABI with an explicit test grant and computes a stack-backed sensor filter. Each platform selection also offers `examples/platform/<platform>/migration/odin`, a Noetic Costmap2D unsigned grid index port with no host imports. Both projects register INT and AOT tests. [Noetic Costmap2D](https://github.com/ros-planning/navigation/blob/f44bb1fc2810399165115cc98b530fe4b9397c18/costmap_2d/include/costmap_2d/costmap_2d.h)

## Build options

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrodin" controller.odin --ros-abi \
  --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --build-receipt -o controller.wasm
```

Export `_start() -> ()` from source. The compiler admits only the exact `uwvm_ros_v2.abi` function with `--ros-abi` and an empty import list otherwise. A module's imports grant no runtime authority. The SDK uses its audited LLVM backend at `-O3 -g`. MTE instrumentation is enabled by default. Use `--no-mte` with a matching untagged compiler and sysroot, or `mte = false` and `WROS_SYSROOTS_NO_MTE` in Xmake. The optional receipt records the selected profile, source and compiler inputs.

The scoped producer supplies Odin's base language runtime for a single freestanding translation unit. The development profile covers stack and global storage accepted by the SDK Wasm backend. Heap allocation, general Odin standard libraries, threads, EH, true memory64, managed-neighbor qualification and vendor-specific execution remain outside this release. Upstream's `wasm64p32` still uses 32-bit pointers. The WasmMTE backend may reject foreign calls in frames with tagged stack owners. The common project keeps its stack-backed computation in a separate helper.

The optional installer component `compiler-source` fetches the pinned Odin build files and base runtime alongside the development package. The release provenance and marker source identify the remaining host LLVM inputs.
