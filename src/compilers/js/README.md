# JavaScript guest interpreter

The frontend links the selected raw ROSv2 imports into the adapted QuickJS 2026-06-04 interpreter and embeds the supplied ES modules. The installed `bin/wrjs` uses its bundled private wasm32 C backend and selected platform modules. When invoking the frontend directly from a source checkout, set `UWVM_ROS_SDK_ROOT` to a native wasm32 C SDK with the required EH and WasmMTE sysroot. The checkout accepts `--platform <id>` to select a platform.

```sh
python3 -B src/compilers/js/driver.py src/examples/js/main.mjs --ros-abi -o app.wasm
python3 -B src/compilers/js/driver.py src/examples/js/guard.mjs \
  --ros-operation capability.open --ros-operation guard.create --ros-operation capability.close -o guard.wasm
```

Import a domain using `import { wr_guard_create } from "uwrosv2/guard"`. All 163 underlying signatures are available for explicit selection. Raw i64 operands use JavaScript bigint and i32 operands use exact unsigned 32-bit numbers. `uwrosv2/memory` exposes the tagged address of an attached ArrayBuffer, allowing the guest to supply actual request bytes, writable result storage and a separate length slot. The application owns these buffers throughout their contract lifetime. The existing `wros` API remains available to scripts that use managed handles and copied data.

The compiler checks the complete Wasm import inventory against the selected operations plus the real-time clock used by QuickJS. Each operation still needs the VM's deployment grants and memory requirements. For example the module exchange protocol requires an eligible shared-memory route, which the single-threaded embedded profile does not provide. Use `--module sub/file.mjs=PATH` for a project dependency and import its virtual name relative to the entry. `--build-receipt` records the engine and module hashes. `--require-qualified` requires a qualified backend release.
