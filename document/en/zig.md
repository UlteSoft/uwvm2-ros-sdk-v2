# Standalone Zig controllers

Install the `zig` development selection with the platform you intend to
authorize. The development driver compiles one Zig 0.16.0 source file to
Core WebAssembly 3.0 with the SDK's WasmMTE backend. It supports wasm32
and wasm64, one thread, Zig error unions, and freestanding applications.
Import the generated module
with `const scene = @import("wros_scene.zig");` and call functions such
as `scene.wr_abi()`. `wrzig` stages this module from its installed SDK.
The generated functions retain the fixed-width signatures documented
in the ABI catalogue.

The linker can resolve wide-integer operations from the selected sysroot's
verified compiler-rt builtins. This profile has no WASI imports, optional
target intrinsics, inline assembly, dynamic loading, or native dependencies. Zig's heap
allocators, threads and libc-dependent applications need a separately
qualified closure. The compiler rejects unresolved runtime symbols.
The backend optimizes with `-O3` and keeps `-g` diagnostics. The Zig
frontend emits IR with its checked debug semantics before this step.

Provide a matching backend toolchain and sysroot with the desired address
width and EH disabled. Place the official Linux x86-64 archive
`zig-x86_64-linux-0.16.0.tar.xz` under
`TOOLCHAIN/share/wros/zig/`. The driver validates its release digest
before extracting a private executable and standard-library source tree.
Install the IR helper from the same SDK revision:

```sh
python3 language/zig/prepare.py --toolchain "$TOOLCHAIN" --host-cxx /usr/bin/c++
```

The IR helper rejects assembly, foreign global storage, thread constructs
and per-definition instrumentation overrides. It marks every supported
function and addressable global, including read-only data, before LLVM
lowers the module. A bounded memory and the exact `uwvm_ros_v2` imports
are checked before the executable is published.

The default marked build requires a local WSEA qualification statement
for one width, the exact SDK and compiler inputs, and the independently
tested VM. `tests/zig_site.py` exercises those inputs with a disposable
test authority. An operator reviews and signs a production site
independently. Pass the resulting profile to `bootstrap.py install
--site-profile`, then compile a local controller:

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrzig" controller.zig -o controller.wasm --build-receipt
```

Use the installed platform's common, extension, or Noetic index-migration
example. From the chosen directory run `xmake f -p wasm-wasip1 -a
wasm32`, `xmake build`, and `WROS_VM=/absolute/path/to/uwvm2-ros xmake
test -j1`. Set the architecture to `wasm64` for a separately signed
wasm64 selection. The extension tests both independent grants on the
platform-controlled driver connection. Compilation grants no ROS access.

For an explicit untagged build, pass `--no-mte --toolchain TOOLCHAIN
--sysroots UNTAGGED_MANIFEST`. Its build receipt records the opt-out and
cannot satisfy the signed `wrzig verify` deployment check. An invalid
or missing signed site stops a default build.

[Official Zig archive and checksums](https://ziglang.org/download/)
