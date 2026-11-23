# Zig 0.16.0

[简体中文](README.zh.md)

The editable upstream directory contains all 21,918 Git blobs from Zig 0.16.0. It includes the frontend, compiler runtime, standard library, CMake and C bootstrap, and the upstream stage-one Wasm seed. The tree and executable modes match upstream commit `24fdd5b7a4c1c8b5deb5b56756b9dbc8e08c86a8`. The project uses the MIT license and retains third-party notices in the distribution. [Upstream tag](https://codeberg.org/ziglang/zig/src/tag/0.16.0) · [Provenance](upstream.json) · [Upstream build instructions](upstream/README.md)

The SDK's `mark_mte.cpp` reads LLVM IR emitted by Zig, checks its target layout and annotates eligible storage for the WROS LLVM backend. This source was recovered from the previous SDK's working tree. Its original bytes are recorded in the provenance file. It needs LLVM development libraries to build. The upstream compiler's CMake recipe requires CMake 3.15 or later and LLVM, Clang and LLD 21.x. Its separate C bootstrap produces the limited stage-two compiler described in the upstream build instructions.

SDK installation of a native Zig compiler, offline reproducibility, target flags, vendor bindings and independent VM runs are pending.
