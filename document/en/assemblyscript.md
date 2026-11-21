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

The default scalar profile supports functions and control flow in a single wasm32 core application. It verifies that the module has zero linear memories, memory imports and data segments. An application may import the exact `uwvm_ros_v2.abi` function through `--ros-abi`. The separate bounded driver profile admits the driver APIs described below.

Each platform selection also installs a migration example at `examples/platform/<platform>/migration/as`. It ports the unsigned grid index used by ROS Noetic Costmap2D. Run `xmake build` and `xmake test -j1` in that directory to check row boundaries, wrapping arithmetic and seeded inputs in both VM engines. The resulting Wasm has no imports. The caller supplies valid coordinates when using the result to access a grid. [ROS Noetic Costmap2D source](https://github.com/ros-planning/navigation/blob/f44bb1fc2810399165115cc98b530fe4b9397c18/costmap_2d/include/costmap_2d/costmap_2d.h)

Each platform also includes `examples/platform/<platform>/extension/as`. Its
Xmake tests exercise the platform and parent permission gates with a private
test channel. Managed objects, a general AssemblyScript runtime, wasm64,
threads, exception handling and vendor-specific operations remain outside
these profiles.

## Bounded ROSv2 driver calls

Import the bindings from `./wros` in the application source. `wras --ros-driver`
supplies this module from the selected SDK. The compiler generates one private,
fixed wasm32 page with separate request, reply, length, handle, and sequence extents.
Default MTE allocates each extent using the VM's managed `memtag.claimz`
instruction. Tags are assigned by the VM's neighbor exclusion policy.
`--no-mte` emits standard Wasm with the same explicit bounds. The generated
module imports no WASIp1 functions.

```ts
import { writeWord, open, opened, close } from "./wros";

export function _start(): void {
    writeWord(0, 0x746e696f6a); // "joint"
    if (open(5) != 0) unreachable();
    if (close(opened()) != 0) unreachable();
}
```

```sh
wras controller.ts --ros-driver --ros-operation capability.open \
    --ros-operation capability.close --build-receipt -g -o controller.wasm
```

At deployment the VM still controls which operation and alias the module can
use. When supplied, repeated `--ros-operation` flags require the final import
set to match exactly. Xmake uses `add_wros_operations` to enforce the same
check. The reserved memory and the generated staging functions stay internal.
`writeByte` and `writeWord` stage little-endian request bytes, and
`submit(capability, size)` submits the specified prefix of the 512-byte
request. `result(capability, sequence)` uses a private sequence slot. The guest
overwrites the consumed bytes after every open and submit, including retries.
Stage the bytes again to retry, or explicitly select
`setRequestWipe(false)` to retain this guest's staging bytes until
`clearRequest()`. The opt-out changes only this module's own staging copy.
`replySize` and `readWord` see only the last successful driver reply. The
next driver call, capability open or close, or an explicit `clearReply()`
overwrites it. `replyRequired` returns a separate required length after
status 90. Reads beyond a successful reply and writes outside the request trap.
If the required capacity exceeds 512 bytes, call
`resultWithCapacity(capability, sequence, capacity)` with the same sequence
and the required capacity, up to 4096 bytes.

Run the source-tree regression through the existing 64 GiB, zero-swap gate.
The replay checks staging erasure, import selection, and failures in both
engines with synchronous MTE, runtime MTE disabled, and an untagged build.
The optional Xmake path also verifies both permission denial configurations.

```sh
PATH_TO_GATE python3 -B tests/assemblyscript_driver.py \
    --commit "$REV" --vm "$VM" --xmake "$XMAKE" --output .tmp/assemblyscript-driver
```

## MuJoCo simulation

The source-tree replay builds an import-free, memory-free controller with the
selectively installed `wras`. UWVM preloads this controller under an explicit
module name. A separate WAT main module calls the scalar `jointTarget` export,
serializes its result, and submits it through its own ROSv2 driver capability.
Both modules run with WASIp1 disabled. Only the WAT module receives scene
authorization.

Run from the SDK source checkout and use the existing 64 GiB, zero-swap
execution gate. Set the paths to the matching VM checkout and binary, the
official MuJoCo distribution, the VM's OpenSSL prefix, and the upstream model
profile and assets.

```sh
PATH_TO_GATE python3 -B tests/assemblyscript_mujoco.py \
    --commit "$REV" --vm-source "$VM_SOURCE" --runtime "$VM" \
    --mujoco "$MUJOCO" --openssl-root "$OPENSSL_PREFIX" \
    --vendor-model "$VM_SOURCE/test/0084.ros-runtime/mujoco_profiles/unitree-go2.json" \
    --vendor-assets "$GO2_ASSETS" --output .tmp/assemblyscript-go2
```

The replay compares 128 simulated steps with direct native MuJoCo stepping.
It also checks that an out-of-range command applies zero steps and that an
external receiver crash after one step leaves the VM able to inspect the
failed channel and disconnect. The receipt records all three cases in both
INT and AOT, the exact assets, build hashes, and the driver-call audit.
Pass `--direct-driver` to build a single AssemblyScript Wasm module that calls
the ROSv2 driver itself. The test enables synchronous WasmMTE checks.
