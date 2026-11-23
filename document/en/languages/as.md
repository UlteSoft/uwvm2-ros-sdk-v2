# AssemblyScript guests

Install `--language as`. The SDK includes Linux x64 Node.js 22.22.3 at `share/toolchains/node/bin/node`. To use another copy of that pinned executable, set `WROS_NODE` to its path. The installed `bin/wras` checks the host executable and its pinned AssemblyScript 0.28.20, Binaryen and long packages. Copy `examples/as` to a writable project for the scalar example.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wras" main.ts --ros-abi -g -o guest.wasm
xmake build
xmake test -j1
```

Import scalar ABI functions from `./uwrosv2/<domain>`. The declarations in `include/u2rosv2/universal/as/uwrosv2` describe all 163 registered imports. The scalar frontend emits a memory-free wasm32 guest with a user-defined `_start(): void`. Its optional host import is `abi`.

Copy `examples/<platform>/as` for a dedicated platform. Compile its `main.ts` with `wras main.ts --ros-driver -o guest.wasm`, or use its Xmake project. It selects `set_wros_profile({as_driver = true})` and reads the observation from bounded staging. The 512-byte request buffer is populated through `./wros`. The platform module can also read a successful driver reply. The supplied samples run offline. An application calling the driver can pass repeated `--ros-operation` options to check its precise import set.

The raw import modules document the VM contract. Linkage and application execution evidence are recorded by revision. [Installation and Xmake](../install-xmake.md)
