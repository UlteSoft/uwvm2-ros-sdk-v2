# Native WROS Rust compiler

[中文版](README.zh.md)

The Linux x86-64 executable `bin/wrrs` loads the Rust 1.98.0 driver from the SDK's `lib` directory. It processes crate roots and launches the same ELF for each rustc session. The second invocation name, `bin/rustc`, accepts raw compiler queries such as `--print target-list`. The driver has built-in definitions for `wasm32-wasip1`, `wasm32-wasip1-threads` and the SDK's `wasm64-wasip1`. Each guest build creates a target sysroot beside the output, compiling `core` (including its macros), `compiler_builtins`, the SDK runtime and the installed bindings from source. The final link uses the packaged `share/toolchains/portable/bin/wasm-ld`. The same ELF is installed as `lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld`, the linker's location for raw rustc sessions using the Wasm flavor.

## Source and changes

`upstream` is the editable source-build closure of the official Rust 1.98.0 source release. Its commit is `88d9e12ae178fab0fb5cc050a94da85685d449ea`. Compiler and library sources, bootstrap, the package manifests of the Rust workspace, the Rust LLVM 22 sources for the host and WebAssembly targets, and the 619 registry packages selected by the root, bootstrap and library locks are present. The release archive, tag, bootstrap component hashes and upstream licenses are recorded in `UPSTREAM.json`. Dependency-specific notices are adjacent to the sources.

Bootstrap reads the release's `.gitmodules` and resolves the paths of registered tools even when building only `compiler/rustc`. This tree includes the `rustbook`, `error_index_generator` and `rust-analyzer` Rust workspaces and the book and reference tool sources behind rustbook's relative dependencies. Registry vendoring covers the compiler build. The rust-analyzer editor extensions, standalone documentation sites, unrelated developer tools, compiler and LLVM test suites, foreign-platform import libraries, binary test fixtures, compressed examples and the schannel/git2 private-key fixtures are outside this selection. The compiler's Cargo lockfiles retain the upstream package hashes. Vendor checksum inventories describe the retained files. The Rust Analyzer LSP-server license links and the LLVM mlgo utility links are materialized as regular files for the Git-object installer.

The SDK changes these compiler inputs.

- `compiler/rustc/src/main.rs` and `wros.rs` select the SDK invocation, compile the explicit Rust crate graph and stage a single reactor export named `_start`.
- `compiler/rustc_llvm/llvm-wrapper/PassWrapper.cpp` calls `WrosIR.h` before LLVM's passes. WROS strips rustc's per-function CPU/feature overrides and marks functions, mutable storage and debug-identified source statics. The marker retains MTE for storage with a suppression annotation and rejects guest inline assembly with instructions. Debug metadata is available when identifying statics, even for stripped output.
- `compiler/rustc_target/src/spec` registers UWVM's 64-bit WASI Preview 1 extension. rustc selects the pointer data layout, target cfg and calling conventions for each ABI.
- `runtime.rs` supplies the upstream Wasm EH language item and a portable guest trap. `lower.py` hands the bitcode to the same packaged SDK LLVM 23 Clang/LLD that implements WasmMTE, then uses the SDK ABI import/signature audit before the native driver publishes the Wasm.

## Build and package generation

Use Linux x86-64, Python 3.12 or later, native C/C++ compilers and development headers, CMake, Ninja, Git and GNU binutils. The source selection downloads the official Rust 1.97.1 host `rustc`, `rust-std` and `cargo` archives from the dated official Rust distribution. The source lock pins their SHA-256 digests. The build checks each archive against `upstream/src/stage0` before extracting it and installs all three into its work directory. An explicit `--rust-bin /path/to/stage0/bin` uses a matching installed compiler, host standard library and Cargo, and skips those downloads. Cargo uses the in-tree vendor directories while LLVM and stage1 rustc build from the included sources.

```sh
work="$PWD/.tmp/rust-release"
python3 -I -B src/compilers/rust/rebuild.py \
    --work "$work/build" --prefix "$work/runtime" --packages "$work/packages" --jobs 8
```

The prefix contains the compiled host executable, its Rust alias and the dynamic compiler libraries required by those executables. The package directory contains one single-member ELF tar.xz per component and `rust-packages.json` with the hashes, installation destinations and system shared-library names. To run verification against an external ABB project before registration, stage the checkout's SDK bindings, native LLVM tools and Xmake rules beside the rebuilt compiler.

```sh
python3 -I -B src/compilers/rust/stage_sdk.py --sdk "$work/runtime" --platform abb
export UWVM_ROS_SDK_ROOT="$work/runtime"
cp -a src/examples/abb/rust/ros1 "$work/abb-ros1"
"$UWVM_ROS_SDK_ROOT/bin/wrrs" --platform abb "$work/abb-ros1/main.rs" -o "$work/abb-ros1/guest.wasm"
```

A release maintainer can register the generated candidate archives in a local checkout.

```sh
python3 -I -B src/compilers/rust/register_release.py --from "$work/packages"
```

## Release status

The host catalog registers the `wrrs` launcher and `librustc_driver-aff9448c053be314.so` from the earlier ABB diagnostic rebuild. Their archive SHA-256 values are `ed3689868ebfd06651c6497c081d90db1d3e876c8653fa96fb74dfd8bbd4db2a` and `8a99747417c5699f26f0c3689e9d16827133dab1145e03642eae58e08527838f`. The installer checks both archives and both ELF payloads, then places the driver on the executable's relative library search path. The driver requires glibc with `GLIBC_2.39` and libstdc++ with `GLIBCXX_3.4.32`. Cold GitHub installation and the separate offline frozen source build reproduced the registered ELF files and both compressed packages byte for byte. ABB guest tests exercised both pointer widths, MTE and native exception handling. The fully bundled candidate also used its installed Xmake and VM for C, C++ and Rust. [Rebuild comparison](../../../document/qualification/abb-rust-ba811556.json) · [Bundled guest runs](../../../document/qualification/abb-1259ec52.json)

## Guest profiles

The default uses wasm32 Core 3, standard Wasm EH, WasmMTE and a single thread. LLVM first receives the MIR without inlining and the bitcode without the default LLVM optimization pipeline. The SDK backend then applies the selected target features and `-O` setting. On EH builds rustc uses `panic=unwind` and can generate Rust cleanup pads for unwind-capable calls. The application defines its own `#[panic_handler]`; the examples trap. The SDK supplies core and compiler intrinsics. Rust std, alloc, a heap-backed Rust panic runtime, `std::panic::catch_unwind`, Cargo dependency resolution, proc macros and Rust thread creation are outside this guest profile.

`--target` sets the pointer width. `--memory64` selects the VM memory64 capability. `--threads` builds wasm32 shared-memory and atomic code and requires a bounded imported `env.memory`; the default maximum is 256 Wasm pages. Provide a memory owner when deploying it. The 64-bit Preview 1 extension supports single-threaded guests. Core MVP requires EH, memory64 and threads disabled. Rust core and builtins are rebuilt for each combination. Only the packaged Core 3/EH/MTE single-thread runtime archives are linked for code requiring external WASI or C++ unwind helpers. The linker reports missing functions for other configurations that request those external helpers.

These source capabilities require production qualification on the relevant interpreter and AOT runtime before publishing a binary support claim. The compiler build does not run the VM or assert that every selectable profile has passed.
