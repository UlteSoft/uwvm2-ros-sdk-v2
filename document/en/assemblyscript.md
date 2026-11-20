# AssemblyScript scalar Wasm

[中文](../zh/assemblyscript.md)

`wras` compiles AssemblyScript directly to core Wasm on a Linux x86-64 build host. The bundled inputs are the stable AssemblyScript 0.28.20, Binaryen 131.0.0 and Long 5.3.2 packages. The SDK records the upstream package integrity and the exact files used by the build. [AssemblyScript release](https://github.com/AssemblyScript/assemblyscript/releases/tag/v0.28.20) · [Compiler inputs](../../third-parties/assemblyscript/release.json)

## Install and build

Set `REV` to the SDK commit you want to install. Set `WROS_VM` to the path of the VM used for the registered Xmake tests.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language as --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT=/absolute/path/printed/by/the/installer
cd "$UWVM_ROS_SDK_ROOT/examples/platform/unitree/common/as"
xmake build
xmake test -j1
```

To build directly from a single `.ts` file, export `_start(): void` and run the compiler from the selected SDK. The example explicitly requests the read-only `uwvm_ros_v2.abi` import. The local Xmake test grants that query to the program under test.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wras" controller.ts --ros-abi --build-receipt -o controller.wasm
```

`--build-receipt` writes `controller.wasm.wros-as.json` with the source hash, artifact hash, compiler release and selected MTE setting. `-g` requests upstream debug names. The Xmake profile accepts `core = "3.0"`, `eh = false` and either MTE setting. The optimizer configuration is fixed for this release.

## Supported source profile

The development package supports scalar functions and control flow in a single wasm32 core application. For the default MTE setting it validates the final binary and verifies that it has zero linear memories, memory imports and data segments. `--no-mte` explicitly changes the requested setting within the same source profile. An application may import the exact `uwvm_ros_v2.abi` function through `--ros-abi`. An application built without that option must have no imports.

Each platform selection also installs a migration example at `examples/platform/<platform>/migration/as`. It ports the unsigned grid index used by ROS Noetic Costmap2D. Run `xmake build` and `xmake test -j1` in that directory to check row boundaries, wrapping arithmetic and seeded inputs in both VM engines. The resulting Wasm has no imports. The caller supplies valid coordinates when using the result to access a grid. [ROS Noetic Costmap2D source](https://github.com/ros-planning/navigation/blob/f44bb1fc2810399165115cc98b530fe4b9397c18/costmap_2d/include/costmap_2d/costmap_2d.h)

Managed objects, a general AssemblyScript runtime, wasm64, threads, exception handling and vendor-specific operations remain outside this profile.
