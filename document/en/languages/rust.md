# Rust

The default ABB Rust selection installs native Rust 1.98.0 `wrrs`, its matching compiler library, and the SDK's Wasm Clang and LLD. The Linux x86-64 host must provide glibc with `GLIBC_2.39`, libstdc++ with `GLIBCXX_3.4.32`, libgcc and zlib. Set `revision` to the full published SDK commit containing the two Rust package entries and run the installer from your project directory.

```sh
python3 -I -B install.py install --commit "$revision" --platform abb --language rust --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
```

`wrrs` compiles an external `no_std` crate using built-in target specifications and the SDK's sources for `core`, its macros and compiler intrinsics. Each build creates its guest sysroot beside the output. Both pointer widths use the packaged linker. There is no Rustup setup step.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrrs" main.rs -o guest.wasm
"$UWVM_ROS_SDK_ROOT/bin/wrrs" --edition 2024 --library sensors ./sensors/lib.rs main.rs -o guest.wasm
"$UWVM_ROS_SDK_ROOT/bin/wrrs" --target wasm64 --memory64 main.rs -o guest64.wasm
```

To build the compiler itself, add `--mode source --jobs 8` to the install command. This selects the editable compiler and LLVM sources and the three official Rust 1.97.1 stage0 archives for x86-64 Linux. The installer verifies the Git/LFS inputs. The rebuild checks each archive against Rust's `src/stage0` lock and installs the bootstrap toolchain in its work directory. Cargo resolves its packages offline. Provide Python 3.12+, native C and C++ compilers with system development headers, CMake, Ninja, Git and GNU binutils. An explicitly supplied `--rust-bin /path/to/1.97.1/bin` uses an existing matching host toolchain and skips the three archive downloads.

Define a `#[panic_handler]` and export `_start`. Edition 2021 is the default. The universal crate is available as `uwrosv2` and `u2rosv2`. In the ABB SDK, `abb` and `wros_observation` name the same adapter. Its `ros1` module exposes the RAPID message and service types. Copy `examples/abb/rust/ros1` outside the SDK and build it with Xmake. [Xmake guide](../install-xmake.md)

The defaults are wasm32, Wasm Core 3, standard Wasm EH, WasmMTE and a single thread. `--no-eh` selects panic-abort code generation. With EH enabled rustc emits unwind-capable cleanup pads and the application supplies the panic handler. The supplied examples trap on panic. This guest environment supplies Rust core and compiler intrinsics. It has no Rust std panic catcher or allocator. `--no-mte` disables WasmMTE independently. `--memory64` gates the VM capability and `--target` selects the pointer ABI. A wasm32 `--threads` build imports a bounded shared memory. The deployment must supply its owner. Rust thread spawning and the wasm64 thread ABI are outside this profile.

For the upstream bindings-only path, select `--mode bindings --no-mte` and provision the upstream `wasm32-unknown-unknown` target before going offline. This Xmake mode uses `WROS_RUSTC` or the upstream rustc on PATH with wasm32, single-threading and abort-on-panic. [Upstream Rust target documentation](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html)

A fresh offline stage1 build from the frozen SDK reproduced both native ELF files and tar.xz archives byte for byte. Candidate ba811556 installed the binary Rust compiler directly from GitHub and compiled ABB wasm32 and wasm64 guests for INT and LLVM AOT. This candidate used external Xmake and VM for execution. [Source and binary comparison, imports and guest cases](../../qualification/abb-rust-ba811556.json)
