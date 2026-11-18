# JavaScript

Select the `js` development package and your platform with the SDK installer. A strict site profile for the C backend supplies the measured toolchain and sysroot. For example, in a pinned SDK checkout run

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language js \
    --prefix "$PREFIX" --site-profile "$C_SITE"
"$PREFIX/$REV/unitree/js/development/bin/wrjs" application.js \
    -o application.wasm --ros-abi --build-receipt
```

Set REV to the full SDK commit, PREFIX to your destination, and C_SITE to the local C site profile approved for this SDK revision.

Each module embeds UTF-8 script source and QuickJS. The target is wasm32 Core 3.0 with EH, one thread, optimization level 3 and debug symbols. Strict WasmMTE is the default. An explicit `--no-mte` build needs its matching toolchain and sysroot. For explicit inputs pass `--toolchain DIR --sysroots MANIFEST`. The build accepts one script up to 1 MiB. There is no native JavaScript or Node.js execution path.

The module imports Preview1 `clock_time_get` for the QuickJS clock. The host can grant the main module access to the real-time clock. File, socket and process imports are excluded. Each selected ROS operation also needs its own VM interface exposure and any required capability grant. With xmake use `set_language("js")` and `add_wros_operations(...)`. See the installed [guard example](../../examples/js/body.js).

Repeat `--ros-operation NAME` for each operation. Selecting `abi` exposes `wros.abi()`. The `capability.open` operation exposes `wros.open(alias)`, which returns an opaque handle on success or a numeric status on failure. The `capability.close` operation exposes `wros.close(handle)`. Other selected operations use `wros[name](handle, requestArrayBuffer, responseCapacity)`. Use `null` only for operations permitting an absent token. The result has a numeric `status`, `data` as an ArrayBuffer or null, and a BigInt `written` length. Scripts encode operation-specific payloads using the common ROSv2 wire contract. The bridge checks the requested extent, copies request and reply buffers in private storage and clears scratch after the call. Each request or reply is limited to 1 MiB. The interpreter heap is limited to 8 MiB with 32 KiB of call-stack budget.

The default script entry runs synchronously. Imports of other JS modules, shell APIs and an event loop are unavailable. A successful build receipt identifies the C compiler that built the interpreter. The accompanying JavaScript receipt also records the script, interpreter sources, selected operations and final artifact digest. Platform-specific permissions and external isolated driver grants are configured by the deployment owner.

The signed C linker exports the application memory as `memory` alongside `_start`. Keep the VM module-link policy closed to imports of this memory. The JS API itself exposes only guest objects and bounded copies. Removing the memory export changes the artifact digest and requires a new verified producer or packaging receipt.
