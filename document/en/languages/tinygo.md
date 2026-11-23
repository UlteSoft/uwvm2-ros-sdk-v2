# TinyGo

The default and explicit binary installs of public candidate `b92c100d` passed. Each built an external project with the installed compiler and Xmake and ran it on both engines of the bundled VM. Independent byte comparisons covered the SDK driver, IR tool and host tool packages. The unmodified installer rebuilt the downloaded frontend sources offline with a separately built LLVM 23.1.5 bootstrap. The public source build, the independent frozen source build and the official frontend produced identical bytes for both tested Wasm guests, which passed INT and AOT. The two source-built host executables differ in their debug line string table and GNU build ID. [Unitree](../../qualification/unitree-b92c100d.json)

The default binary selection installs `wrtg`, `prepare-ir`, the verified official TinyGo 0.38.0 frontend and its WASIp1 runtime, plus Go 1.24.2. Source mode rebuilds the SDK driver, the LLVM 23.1.5 IR tool, and the TinyGo frontend itself. The latter is compiled from the editable TinyGo tree, Espressif LLVM 19.1.2 and 28 vendored Go modules. The installer skips the upstream TinyGo executable in source mode. Both modes use the SDK’s packaged Clang and wasm-ld to generate guest code. [Frontend inputs and rebuild commands](../../../src/compilers/tinygo/README.md)

The profile targets wasm32 with 32-bit Go int, pointers and uintptr, Core 3.0, EH and MTE enabled, Wasm threads off. `wrtg --print-target` prints the actual settings. `--go-word-bits 32` checks the data model. `--memory64` and `--no-memory64` govern the VM's grammar independently of the emitted wasm32 memory. This target uses TinyGo's conservative collector, scheduler=none and wasi-legacy command startup. Wasm64, Wasm threads, scheduled goroutines, a C library for arbitrary cgo programs and MVP are outside this target's current scope.

The tagged collector claims each allocation, preserves tags in mutator pointers, normalizes offsets for collector metadata, scans live tags and releases whole retired extents. The LLVM target handles eligible stack allocations and mutable globals. `--no-mte` selects TinyGo's original conservative allocator. `--eh` assembles the module-owned terminal panic tag with the Wasm exception-handling feature. `--no-eh` selects upstream panic=trap and omits that assembly. TinyGo 0.38.0 on wasm32 runs ordinary deferred calls on return and has no panic stack unwinder. The Wasm panic runtime dispatches directly to its terminal handler at every optimization level. [TinyGo's recover implementation](https://github.com/tinygo-org/tinygo/blob/733a17d470870afc9c821524ce291ec5062d682b/compiler/defer.go)

Source installation requires GNU Make, CMake, Ninja and a host C/C++ compiler. `--bootstrap /absolute/llvm-prefix` or `WROS_LLVM_CONFIG=/absolute/llvm-config` can provide the LLVM 23.1.5 development tree for the IR tool. The native frontend uses its own vendored LLVM 19.1.2. For the default binary install, run these commands in a new project directory.

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
revision=b92c100dcb2586846797eb40ddb357764b1cd26e
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform unitree --language tinygo --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
cp -R "$UWVM_ROS_SDK_ROOT/examples/unitree/tinygo" unitree-guest
cd unitree-guest
wrtg . -o direct.wasm
xmake build
xmake test -j1
```

The selected prefix contains uwvm2-ros for execution tests. The direct command is `wrtg . -o app.wasm`. It accepts `-g` and TinyGo optimization levels `-O0`, `-O1`, `-O2`, `-Os` and `-Oz`. Standard Go and TinyGo share the same user module sources, public u2rosv2 imports and Unitree Go2/HG CDR codecs. The example calls ABI in the actual VM and exercises locally constructed LowState values. The project uses real WASIp1 clocks and randomness where its reachable runtime requests them. Hardware acquisition requires an operator-provisioned ROS 2 endpoint. [TinyGo upstream](https://github.com/tinygo-org/tinygo/tree/733a17d470870afc9c821524ce291ec5062d682b) [Unitree ROS 2 messages](https://github.com/unitreerobotics/unitree_ros2/tree/66ae09858245ac3d2231c0cc209e36a88f8d7d03/cyclonedds_ws/src/unitree)

## ABB ROS 1

Select `--platform abb --language tinygo` from a revision containing the ABB Go module. Copy `examples/abb/tinygo` from the installed SDK into your project directory. Build it with `wrtg . -o direct.wasm` or the installed Xmake. The example reads the scene ABI, transfers a RAPID symbol request and response, and round-trips an EGM channel report. The module provides all 70 ROS 1 body types, identifiers and handshake MD5s. [Installation, domain packages and wire rules](../../../include/u2rosv2/platform/abb/go/README.md)

## Franka ROS 2

Select `--platform franka --language tinygo` and copy `examples/franka/tinygo` into an external project. The example reads a gripper feedback envelope and a 0.42 m spine GetPosition response carried by a service event. Build with `wrtg . -o direct.wasm` or with the selected installation’s Xmake. [Franka Go and TinyGo manual](../../../include/u2rosv2/platform/franka/go/README.md)
