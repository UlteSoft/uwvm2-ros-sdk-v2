# Rust core applications

`wrrs` builds a Rust 2024 application root, its Rust modules and explicitly selected local libraries into a wasm32 reactor. This profile uses Core 3.0, one thread and `panic=abort`. It supports `core`, compiler builtins and the SDK's raw ROS imports. Programs requiring Cargo dependency resolution, procedural macros, `alloc`, `std`, unwinding or memory64 need a different runtime closure.

## Install and compile

Install the `rs` selection for a registered platform, for example `unitree`. A signed development site supplies the exact producer, sysroot and compilation settings reviewed for this SDK and VM.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language rs \
  --prefix "$PREFIX" --site-profile "$SITE"
SDK="$PREFIX/$REV/unitree/rs/development"
"$SDK/bin/wrrs" "$SDK/examples/rs/body.rs" --build-receipt -o robot.wasm
```

Place the pinned Rust 1.98.0 installation at `TOOLCHAIN/libexec/wros/rust` and its host C++ compiler at `TOOLCHAIN/libexec/wros/rust-host/c++`. The host compiler builds the SDK's IR instrumentation tool. The reviewed site selects the Linux x86-64 hosts, WasmMTE LLVM 23.1.5 development files, target sysroot, VM digest, and `-O3 -g` settings. Installation checks the signed row and the host library digests. See [local release qualification](memory-qualification.md).

For a site operator's qualification run, select `--language rs --target wasm32 -O3 -g` with `tools/wasm/memtag/qualify_local_c.py`. Supply the standard approved producer, MTE sysroot and VM digests, plus `--approved-rust-inputs-sha256` (canonical map of `rustc` and `host_cxx` digests), `--rust-plain-sysroots` and its `--approved-rust-plain-sysroots-sha256` digest. The plain control must use the same compiler and source closure. Sign the resulting local release using the site's WSEA trust policy.

A minimal `app.rs` uses the predeclared `wros_scene` crate. The caller's VM policy must grant the ABI query used here.

```rust
#![no_std]

#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    let version = unsafe { wros_scene::wr_abi() };
    assert_eq!(version, 2);
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    core::arch::wasm32::unreachable()
}
```

## Compiler controls

Use `--library arrayvec /path/to/arrayvec/src/lib.rs` to compile a local
`no_std` library with the same compiler settings and MTE policy as the
application. Repeat the option in dependency order. For example, a second
library can use `arrayvec` if it appears after that declaration. The
application refers to the libraries by their declared crate names.

| Option | Meaning |
| --- | --- |
| `--rustroot PATH` | Linux x86-64 Rust 1.98.0 installation matching `language/rust/toolchain-inputs.json`. |
| `--library NAME CRATE_ROOT` | Build a declared Rust 2024 source crate. Repeat in dependency order. |
| `--toolchain PATH` | WasmMTE Clang, linker and corresponding LLVM development files. |
| `--sysroots FILE` | Matching sysroot build receipt. Repeat to supply different profiles. |
| `--target wasm32 --core 3.0 --no-eh` | Current supported target. These values are the Rust defaults. |
| `--mte` or `--no-mte` | Choose the instrumentation profile for all crates and the matching final sysroot. MTE is enabled by default. |
| `-O0`, `-O1`, `-O2`, `-O3` | LLVM optimization level after instrumentation policy selection. The signed site uses `-O3`. An explicit producer defaults to `-O2`. |
| `-g` | Preserve source locations for guest code generation. |
| `--host-cxx FILE` | Host C++ compiler for the LLVM IR tool. Defaults to `/usr/bin/c++`. |
| `--print-identity` | Print the profile, compiler and source digests, per-crate IR and object digests, and local suppression inventory. |
| `-o FILE.wasm` | Publish the final module after link and import checks. |

The producer rebuilds `core` and `compiler_builtins` from the vendored upstream `rust-src` release in a fresh private sysroot. It keeps Rust metadata there, disables MIR optimization and delays LLVM optimization until after source-level instrumentation choices have been applied. Rust's compiler-internal options support this build lifecycle. User crates remain restricted to stable source features. The final audit checks imported module names, fields and signatures.

With MTE enabled, `#[unsafe(link_section = ".wros.no_memtag")]` requests a compiler proof. The current proof accepts a single block of integer SSA arithmetic, comparisons, selections, casts and a scalar return. The proof admits native Wasm integer widths up to 64 bits. Pointer parameters, wide integers, stack slots, memory access and calls retain instrumentation. The backend keeps the sanitizer enabled when lowering proven code so any storage introduced later remains eligible for tagging. Mutable statics retain tagging even when their export name starts with `__wros_no_memtag_`. The build receipt lists requests accepted by the proof and requests for which instrumentation was retained. The compiler applies the rule to user code, ROS bindings and runtime crates before LLVM optimization. Safe functions can contain unsafe blocks or call safe wrappers around raw pointer operations. Such boundaries and Rust reference types supply no elision proof. Values that exist entirely in registers have no linear-memory allocation to tag. Use `--no-mte` to choose the explicit whole-program profile.

For xmake use `set_language("rs")`, one crate root in `add_files`, and the installed signed site. The `examples/rs` project builds with `UWVM_ROS_SDK_ROOT="$SDK" xmake f -p wasm-wasip1 -a wasm32 -y` then `UWVM_ROS_SDK_ROOT="$SDK" xmake`. For explicit producer selection, supply `WROS_RUSTROOT`, `WROS_TOOLCHAIN` and `WROS_SYSROOTS` together. The project may declare its local Rust modules from that root. See the [xmake reference](xmake.md).
