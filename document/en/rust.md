# Rust core applications

`wrrs` builds one Rust 2024 crate root and its Rust modules into a wasm32 reactor. This profile uses Core 3.0, one thread and `panic=abort`. It supports `core`, compiler builtins and the SDK's raw ROS imports. Programs requiring Cargo dependency resolution, procedural macros, `alloc`, `std`, unwinding or memory64 need a different runtime closure. No such closure is installed by this selection.

## Install and compile

Choose the `rs` language and a platform which declares it, such as `unitree`. Supply the installed Linux x86-64 Rust 1.98.0 prefix, the SDK's LLVM 23.1.5 WasmMTE producer with its development headers and libraries, and a completed sysroot receipt matching the requested profile. A C++ compiler on the build machine compiles a build-time LLVM tool. The Rust application and its libraries compile to Wasm.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language rs --prefix "$PREFIX"
SDK="$PREFIX/$REV/unitree/rs/development"
"$SDK/bin/wrrs" app.rs --rustroot "$WROS_RUSTROOT" --toolchain "$WROS_TOOLCHAIN" \
  --sysroots "$WROS_SYSROOTS" --no-eh -O3 -g -o robot.wasm
```

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

| Option | Meaning |
| --- | --- |
| `--rustroot PATH` | Linux x86-64 Rust 1.98.0 installation matching `language/rust/toolchain-inputs.json`. |
| `--toolchain PATH` | WasmMTE Clang, linker and corresponding LLVM development files. |
| `--sysroots FILE` | Matching sysroot build receipt. Repeat to supply different profiles. |
| `--target wasm32 --core 3.0 --no-eh` | Current supported target. These values are the Rust defaults. |
| `--mte` or `--no-mte` | Choose the instrumentation profile for all crates and the matching final sysroot. MTE is enabled by default. |
| `-O0`, `-O1`, `-O2`, `-O3` | LLVM optimization level after instrumentation policy selection. Default is `-O2`. |
| `-g` | Preserve source locations for guest code generation. |
| `--host-cxx FILE` | Host C++ compiler for the LLVM IR tool. Defaults to `/usr/bin/c++`. |
| `--print-identity` | Print the profile, compiler and source digests, per-crate IR and object digests, and local suppression inventory. |
| `-o FILE.wasm` | Publish the final module after link and import checks. |

The producer rebuilds `core` and `compiler_builtins` from the vendored upstream `rust-src` release in a fresh private sysroot. It keeps Rust metadata there, disables MIR optimization and delays LLVM optimization until after source-level instrumentation choices have been applied. Rust's compiler-internal options support this build lifecycle. User crates remain restricted to stable source features. The final audit checks imported module names, fields and signatures.

For local suppression use `#[unsafe(link_section = ".wros.no_memtag")]` and `#[inline(never)]` on the function whose code should omit instrumentation. For a mutable static, use an explicit symbol such as `#[unsafe(export_name = "__wros_no_memtag_state")]`. Rust emits a static’s `link_section` as custom-section data on Wasm, so it cannot select the corresponding global. A marked function stays out of callers' inline expansions. Combining this request with `#[inline(always)]` is an error. Independent compiler proofs may remove tag operations from ordinary bounded accesses. Disabling guest instrumentation is distinct from changing how an operator configures the VM.

For xmake use `set_language("rs")`, one crate root in `add_files`, and `WROS_RUSTROOT`. The project may declare its local Rust modules from that root. See the [xmake reference](xmake.md).
