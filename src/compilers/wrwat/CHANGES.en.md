# wrwat source history

[中文](CHANGES.zh.md) · [Machine-readable upstream revisions and checksums](UPSTREAM.json)

The package root is a Cargo workspace. `src/main.rs` validates the assembled module and publishes the output. `src/cli.rs` interprets the selected profile. `src/policy.rs` validates imports against the installed SDK catalogue. The SDK introduced packed linear-memory instructions in `d72ffb5` and its native command in `ad5cf14`. Use `git log --follow -- src/compilers/wrwat/src/main.rs` from the SDK root to inspect subsequent edits. [Packed instructions](https://github.com/UlteSoft/uwvm2-ros-sdk-v2/commit/d72ffb5d181dce67b5caa72d0633967899fc80ea) · [Native command](https://github.com/UlteSoft/uwvm2-ros-sdk-v2/commit/ad5cf148ee70a79afa4f09333227588832678a37)

## Changes carried by the SDK

1. `changes/01-reader-feature.patch` reproduces the packed WasmMTE reader and its distinct feature gate in the pinned wasm-fuzzer fork. It covers binary decoding, operator definitions and operand validation. [Reader revision](https://github.com/UlteSoft/wasm-fuzzer/tree/5beb8556ee40e249cd5f26449784a79f4616ee5c/vendor/wasmparser-memtag)
2. `changes/02-sdk-text-encoding.patch` adds WAT keywords and memory-name resolution to wast, packed instruction emission to wasm-encoder, and validation of the managed lifetime operators to the reader.

Both diffs already apply to the checked-in build sources. To reproduce their history, unpack the three official crates identified by `UPSTREAM.json` into a clean directory, at the indicated `vendor/` paths. Verify each crate checksum. Run `git apply` on the two diff files in numeric order there, then compare the resulting `vendor/` tree with this workspace. The baseline uses the published crate layout, including Cargo's normalized manifests. [Upstream release](https://github.com/bytecodealliance/wasm-tools/releases/tag/v1.263.0)

Other Rust dependencies are pinned by `Cargo.lock`. The `registry/` directory carries their build sources, original notices, and Cargo checksums for offline use.

## Rebuilding Linux host tools

Run these commands from a Git LFS checkout of the SDK, or use the installer’s WAT source selection to materialize the inputs for one host. Python 3.11+, native `cc`, binutils, glibc development files, libgcc and zlib support the compiler and Cargo build scripts. The recipe fetches the Rust 1.98.0 archives from the official URLs in the host lock, verifies the archives and selected members, and uses the checked-in Cargo registry offline. The four musl builds link with the Rust distribution’s ELF linker, LLD 22.1.8, and the musl startup objects and libraries from the target’s Rust standard library.

```sh
python3 -I -B src/compilers/wrwat/rebuild.py --output .tmp/wrwat-native
python3 -I -B src/compilers/wrwat/rebuild.py --host linux-armhf --output .tmp/wrwat-armhf
python3 -I -B src/compilers/wrwat/package_release.py --host linux-armhf \
  --executable .tmp/wrwat-armhf --output-root .tmp/wrwat-release
```

The first command builds for the ABI of the running Python interpreter. On x86-64, the second command can target any of the five SDK hosts listed below. A native source installation uses its host’s GNU Rust bootstrap. Supply `--rust-bin /path/to/rust/bin` to use an installed matching toolchain with its host standard library. The target archive is still selected for a musl build. Use `--jobs N` to set Cargo parallelism and `--work DIR` to put temporary build products on a writable filesystem. Each build requires a new output path.

- `linux-x86_64` builds and runs `x86_64-unknown-linux-gnu` with the native glibc linker driver and GNU strip. Its original bootstrap is pinned in `bootstrap.json`.
- `linux-i686` uses `i686-unknown-linux-gnu` to build `i686-unknown-linux-musl`. Both require a Pentium 4 class CPU with SSE2.
- `linux-aarch64` uses `aarch64-unknown-linux-gnu` to build `aarch64-unknown-linux-musl`. The matching official AArch64 musl host toolchain is also accepted with `--rust-bin` on a compatible userspace.
- `linux-arm` uses `arm-unknown-linux-gnueabi`, which requires an ARMv6 or newer soft-float GNU userspace. Its static output targets `armv5te-unknown-linux-musleabi`. For ARMv5TE hardware, build the executable on x86-64 or an ARMv6+ builder.
- `linux-armhf` uses `armv7-unknown-linux-gnueabihf` to build `armv7-unknown-linux-musleabihf`. The static output uses the ARMv7-A hard-float ABI and VFPv3-D16.

Rust 1.98.0 publishes target libraries for all four musl targets. Among those four triples it publishes native rustc and Cargo for AArch64 musl only. The SDK’s matching GNU distributions provide native compilers for the other ABIs subject to the CPU requirements above. Each `bootstrap/linux-*.json` identifies the native compiler, Cargo, native standard library and separate target standard library by upstream URL and SHA-256. Maintainers can regenerate each inventory with `lock_bootstrap.py <dated-channel-manifest> --host <sdk-host>` after placing the four official archives at the recorded paths. [Rust 1.98.0 distribution manifest](https://static.rust-lang.org/dist/2026-08-20/channel-rust-1.98.0.toml) · [Rust 1.98.0 target specifications](https://github.com/rust-lang/rust/tree/88d9e12ae178fab0fb5cc050a94da85685d449ea/compiler/rustc_target/src/spec/targets)

The packaging command verifies the executable’s ELF ABI, loadable entry point, compiler and linker identity. It also verifies static linkage for the musl targets and the ARM CPU and floating-point attributes. It writes the archive, release record and WAT selection under the requested output root. An existing host manifest retains its other languages. Omit `--output-root` to update the checkout. Each host installs its `src/compilers/wrwat/release/<host>.json` as `third-parties/wat-mte/release.json`.
