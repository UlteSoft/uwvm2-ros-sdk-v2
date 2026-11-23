# TypeScript guests

Install `--language typescript`. The SDK uses the included Linux x64 Node.js 22.22.3 at `share/toolchains/node/bin/node`. Set `WROS_NODE` only to select another copy of the pinned executable. Copy `examples/typescript` to a writable project. The installed `bin/wrts` runs the pinned TypeScript 5.9.3 compiler with strict ES2022 checking. It compiles the emitted modules with the same private QuickJS backend used by JavaScript guests.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrts" main.ts filter.ts --ros-operation abi -o guest.wasm
xmake build
xmake test -j1
```

Pass the entry module first, then the other `.ts` files in the project. Use `--project-root` when they share a root above the entry directory. In Xmake use `add_files("main.ts", "filter.ts")` and `set_wros_entry("main.ts")`. Select needed host imports with `--ros-operation` or `add_wros_operations`. The type checker exposes the corresponding raw functions from `uwrosv2/<domain>`. The declarations use `bigint` for i64 and `number` for i32. QuickJS requires the WASIp1 real-time clock. The supplied projects request it for local execution.

Copy `examples/<platform>/typescript` to run a dedicated decoder. Its declarations come from `include/u2rosv2/platform/<platform>/typescript` and its implementation is bundled from the same revision's JavaScript binding. The platform code accepts a `Uint8Array` containing the documented wire record. [Installation and Xmake](../install-xmake.md)
