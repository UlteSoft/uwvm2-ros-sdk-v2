# Build a Lua application for u2ros

`bin/wrlua` packages one Lua text file with the Lua 5.4.9 interpreter. The resulting WebAssembly module exports `_start`. Lua source is decoded and executed inside the VM. The build machine runs Python and the Wasm cross-compiler. It does not need an installed Lua interpreter.

From the Lua development installation, set `PRODUCER` to the Wasm-only compiler prefix and `RECEIPT` to its matching sysroot receipt. This example reads the ROSv2 ABI and checks a median calculated in the guest.

```sh
bin/wrlua examples/lua/body.lua --ros-abi \
  --toolchain "$PRODUCER" --sysroots "$RECEIPT" -o body.wasm
```

## Build options

| Argument | Meaning |
| --- | --- |
| `SCRIPT` | One Lua text chunk, up to 1 MiB. NUL bytes and binary chunks are rejected. |
| `-o FILE`, `--output FILE` | Destination for the linked Wasm module. The output directory must exist. |
| `--mte`, `--no-mte` | Enable memory tagging (default) or explicitly disable it for the interpreter and its runtime. Select the matching sysroot. |
| `--toolchain DIR` | Prefix containing the SDK's WasmMTE-capable Clang and linker. |
| `--sysroots FILE` | Build receipt for matching target headers and libraries. |
| `--target wasm32` or `--target wasm64` | Guest pointer width. The default is wasm32. |
| `--guest-seed UINT32` | Use a guest-local, publicly known unsigned 32-bit seed for hash initialization, sort pivots and the initial math PRNG state. The final guest imports no clock. With `--ros-abi`, its only import is `uwvm_ros_v2.abi`. This mode enables repeatable pseudo-random sequences and offers no unpredictable hash seed for adversarial table keys. |
| `--ros-abi` | Register `wros.abi()` in Lua and link its ROSv2 import. |

This interpreter build uses Wasm Core 3.0, C++ exceptions for Lua protected calls, WasmMTE by default and a single guest thread. Optimization and debug symbols are enabled together. Each call of `_start` creates a fresh Lua state with a 16 MiB limit on live Lua heap allocations. Set the overall Wasm memory and execution limits in the VM. Embedded chunk text is part of the compiled module and can be read from the artifact.

## Libraries and host permissions

The guest exposes the base, table, string, math, UTF-8 and coroutine libraries. General file and OS access, package loading, debug library access, and the base functions `dofile`, `loadfile`, `load`, `print` and `warn` are unavailable. Uncaught Lua errors and syntax errors trap the guest. An application can catch errors raised inside `pcall` and continue. Coroutines share the guest thread.

By default, the runtime uses Preview1 `clock_time_get` for upstream seeding and sort pivot selection. A wasm64 build imports `clock_time_get_wasm64`. The VM must expose this import for linking. Realtime and monotonic read grants can be controlled separately. If the VM denies an individual read, Lua can still initialize a seed or select a pivot. The guest-seeded mode also disables the clock lookup in the single-threaded C library’s timed-wait fallback. The linker output is checked against the permitted imports for the selected mode. Use a cryptographic source for secrets.

`--ros-abi` adds the import `uwvm_ros_v2.abi`. A VM deployment must bind the guest to a scene and expose `abi` there. The build flag only changes the guest API. Use repeated `--ros-operation NAME` arguments to include specific bindings. Xmake accepts the same names in `add_wros_lua_operations(...)`.

`capability.open` supplies `wros.open(alias)`, which returns a status and an opaque capability or nil. `capability.close` supplies `wros.close(capability)`. For each selected message operation, call `wros["domain.operation"](capability, request_bytes, response_capacity)`. It returns the numeric status, a binary Lua string when the VM supplies a reply, and the reported byte count. A query of an uncompiled family through `permission.report` or `module.permission.report` returns status 95 with a page whose supported flag is false. An unknown exact function returns 95 and nil. A denied query returns nil. If the VM reports that the buffer is too small, use the reported size to retry. Use nil as the capability for operations whose VM contract allows token zero. Pack and unpack the little-endian message described in `share/abi/ros.json`. Each call uses guest-owned scratch within the Lua heap budget. It erases the scratch after the call, including when allocating the returned string fails. The application controls the lifetime of its Lua strings.

The installed `examples/lua/guard.lua` uses five imports. Build it with `--guest-seed 1` and select `capability.open`, `capability.close`, `guard.create`, `guard.trigger`, and `guard.take`. Expose those functions to the module and grant the three guard actions to its `signal` alias. A denied import prevents startup; a missing resource grant returns a status to Lua.

For example, from the directory containing `body.wasm`, set `VM` to the u2ros VM executable. The following command runs the example on a VM with Core 3.0 support and the SDK's WasmMTE instructions enabled.

```sh
"$VM" --wasm-set-main-module-name main --runtime-int \
  --wasm-feature-enable-exceptions --wasm-feature-enable-tail-call \
  --wasm-feature-enable-simd \
  --wasip1-single-create main --wasip1-single-enable main \
  --wasip1-single-interface main clock_time_get allow \
  --wasip1-single-grant main realtime-clock \
  --ros-scene-create robot --ros-scene-bind robot main \
  --ros-scene-interface robot abi allow --run body.wasm
```
