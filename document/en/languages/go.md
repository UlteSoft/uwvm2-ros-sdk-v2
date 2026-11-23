# Standard Go

Select `--platform unitree --language go --mode source` for the native `wrgo` command. It builds a Go module with Go 1.24.2's package loader, compiler, assembler, linker and standard library. Source mode rebuilds the compiler, assembler, linker and SDK command with the pinned Linux x86-64 Go bootstrap. The pinned public candidate below defaults to the verified binary package set. The historical Go register-only expression producer accepted a restricted scalar subset. Its binaries and its test evidence are from that earlier implementation.

`wrgo --print-target` reports the selected axes. The default targets Core 3.0, a wasm32 linear memory, WasmMTE on, EH on and Wasm threads off. The Go wasm port uses 64-bit Go int, pointers and uintptr with 32-bit instruction addresses. The scene import registration uses its own explicit i32 and i64 types. `--go-word-bits 64` checks the Go data model. `--memory64` and `--no-memory64` choose the VM feature policy independently of this module's 32-bit memory. The wasm64 ABI, a 32-bit standard Go data model, threaded Wasm and MVP require further backend work.

With `--mte`, the runtime claims each dynamically allocated goroutine stack segment, keeps the tag in stack bounds and interior pointers, and releases the complete segment before returning it to Go's allocator. The assembler emits packed WasmMTE v1 `memtag.claimz` and `memtag.release`. The linker caps memory at 256 MiB for this profile. Ordinary Go heap objects, individual stack frames, the static bootstrap stack and globals have no per-object protection in this implementation. `--no-mte` selects the upstream stack ownership path. Go defer and recover keep their Go semantics. With `--eh`, terminal unrecovered Go panics throw a module-defined Wasm tag. With `--no-eh`, unrecovered panics use Go's usual fatal path.

In your own directory, use Linux x86-64 with Python 3.11+, Git and curl. The installer supplies Xmake and the INT/AOT build of uwvm2-ros. The following commands select the verified public commit.

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
revision=b92c100dcb2586846797eb40ddb357764b1cd26e
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform unitree --language go --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
cp -R "$UWVM_ROS_SDK_ROOT/examples/unitree/go" unitree-guest
cd unitree-guest
wrgo . -o direct.wasm
xmake build
xmake test -j1
```

The native command also accepts `wrgo . -o app.wasm`, `-g`, `-O0` and `-O2`. An application declares the public modules in its go.mod. The SDK creates a temporary go.work referencing the installed packages and preserves the user's other workspace module paths and replacements. The compiler defaults to offline resolution and honors an explicit GOPROXY. The public import paths are `github.com/UlteSoft/uwvm2-ros-sdk-v2/u2rosv2` and `github.com/UlteSoft/uwvm2-ros-sdk-v2/unitree/unitreego`. Use the first package's naturally typed functions, including `u2rosv2.ABI()`. Its documentation gives the exact registration, authority, integer widths and memory/result rules for every operation.

The Unitree project reads the real scene ABI, then encodes and decodes full Go2 LowState values with the nested IMU, 20 motors, BMS and remaining fields. Its local values exercise the codec. Live acquisition requires a ROS 2 deployment providing serialized samples. The test profile configures only linked WASIp1 interfaces and explicit startup grants, with an empty environment and no filesystem mounts. It can grant guest argv, environment sizes/data, monotonic/realtime clocks, randomness, process exit, stderr and a monotonic timer. Other linked WASIp1 interfaces receive the deny state. Runtime qualification for each native product and feature mode is pending. [Go upstream](https://github.com/golang/go/tree/49860cf92a9a3ba434d2bc393faaefabe48d181e) [Unitree ROS 2 schema](https://github.com/unitreerobotics/unitree_ros2/blob/66ae09858245ac3d2231c0cc209e36a88f8d7d03/cyclonedds_ws/src/unitree/unitree_go/msg/LowState.msg)

## ABB ROS 1

Select `--platform abb --language go` from a revision containing the ABB Go module. Copy `examples/abb/go` from the installed SDK into your project directory. Build it with `wrgo . -o direct.wasm` or the installed Xmake. The example reads the scene ABI, transfers a RAPID symbol request and response, and round-trips an EGM channel report. The module provides all 70 ROS 1 body types, identifiers and handshake MD5s. [Installation, domain packages and wire rules](../../../include/u2rosv2/platform/abb/go/README.md)

## Franka ROS 2

Select `--platform franka --language go` and copy `examples/franka/go` into an external project. The example transcodes the independent Elbow frames and decodes a semantic-component FrankaRobotState with owned joint names and positions. Build with `wrgo . -o direct.wasm` or with the selected installation’s Xmake. [Franka Go and TinyGo manual](../../../include/u2rosv2/platform/franka/go/README.md)
