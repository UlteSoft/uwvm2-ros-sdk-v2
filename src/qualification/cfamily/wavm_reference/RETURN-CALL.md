# Direct WebAssembly tail calls and SIMD lane accesses in the WAVM reference

After the four base layers on WAVM `cd7107792bf69ffe62d245ab9479ec5421f13c75`, apply the fifth patch for direct `return_call` and the sixth for x86-64 tail transfers and SIMD lane access widths. Use `--enable return-call` with the pinned LLVM 23 x86-64 Linux build. Both wasm32 and wasm64 guests use this host ABI. [Build instructions](UPSTREAM.md) · [Fifth patch](core-return-call.patch) · [Sixth patch](tailcc-simd-lanes.patch) · [中文](RETURN-CALL.zh-CN.md)

The fifth patch SHA-256 is `8f9d1beb5ff1b5c9e4b50d151aaf0cd4bd44158760391fd6cb35c0e7fa9aaf13`. After all five layers, `Lib/LLVMJIT/EmitCore.cpp` has SHA-256 `92ccff37730dbbdd3170e9ccbd15a3295d316d6a5a300b26a662071b50c394f0` and `Lib/IR/Validate.cpp` has SHA-256 `28a3c707bb28d67941029256498804a15d5da4dcc15e799b54f39dcf8fd41065`.

```sh
git -C WAVM apply "$WAVM_REFERENCE_DIR/core-return-call.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/tailcc-simd-lanes.patch"
(cd WAVM && sha256sum -c "$WAVM_REFERENCE_DIR/PATCHED-SOURCES.sha256")
```

The sixth patch SHA-256 is `2e30dee8b7d8a5344ba503bc5cc1393901cae4285e340165b25af4c4eb4b475e`. The manifest covers all 26 patched source files after the six layers and has SHA-256 `d8ebe9c29b44165b65b921a20629efc3741c9baae08858c48ae9d9bc4e8003c2`. [Patched source hashes](PATCHED-SOURCES.sha256)

After rebuilding, run the original cJSON file with the same iteration count in both configurations.

```sh
wavm-build/bin/wavm run --nocache --enable return-call --enable wros-ownership --enable memtag-soft-debug "$GUEST" 100
wavm-build/bin/wavm run --nocache --enable return-call --enable wros-ownership "$GUEST" 100
```

A static decode of each frozen cJSON module found three direct `return_call` instructions. Each default common C module contains one. Across these four files, opcode `0x12` was the only decoded operation missing from the four-layer reference. The binary reader reports `return_call_indirect` and `return_call_ref` by name if encountered.

The validator resolves the function index, consumes the callee’s arguments, checks its result tuple against the enclosing function’s results and marks the continuation unreachable. Defined functions and imported functions with the Wasm calling convention use the same lowering. Host imports enter through WAVM’s Wasm-callable wrappers. The callee’s exceptions and traps propagate past the discarded frame. [Core validation rules](https://webassembly.github.io/spec/core/valid/instructions.html) · [Core execution rules](https://webassembly.github.io/spec/core/exec/instructions.html)

## Tail-call lowering

The five-layer build failed a valid chain with 1, 14 and 1 explicit parameters and six mixed results. Its first native jump omitted five outgoing stack arguments. In the pinned LLVM x86 backend, `musttail` on this calling convention selects a sibling call that assumes the stack arguments already occupy the callee’s slots. [Pinned x86 call lowering](https://github.com/llvm/llvm-project/blob/4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89/llvm/lib/Target/X86/X86ISelLoweringCall.cpp)

The sixth layer preserves `musttail` through WAVM’s scalar optimizations so the call stays next to its return. Before native emission or LLVM IR export it verifies that the return forwards the entire call result, then selects `tail call tailcc`. LLVM guarantees a tail transfer for this shape on x86-64 with fixed-arity `tailcc` endpoints and static relocation. The direct call uses the callee’s exact prototype. The caller may have different parameters. The backend places outgoing register and stack arguments and relocates the return address when the argument areas differ. [LLVM call contract](https://github.com/llvm/llvm-project/blob/4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89/llvm/docs/LangRef.rst) · [x86 platform conditions](https://github.com/llvm/llvm-project/blob/4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89/llvm/docs/CodeGenerator.rst)

The ABI result forwards the context pointer and any direct results. For three or more Wasm results the callee writes the tuple into that context. Wasm functions, call sites and host-entry thunks use the same convention across feature flags. The host profile requires Linux ELF x86-64 with 64-bit pointers. Each endpoint supports up to 4,094 explicit parameters, leaving space for alignment within x86’s 16-bit callee-pop immediate. Larger signatures use the existing fast convention for ordinary calls. JIT cache version 7 and the native instance symbol `biasedInstanceId.tailcc.v2` distinguish the corrected objects.

## SIMD lane access widths

In the tagged wasm32 LZ4 module with SHA-256 `3c021383817f0895ad8cd09ebdb3d81c11d1ab42aad0959cfe66f4699579968e`, the five-layer build trapped at `__original_main+1567`. The instruction at byte offset `0x15fa` is `v128.store64_lane` with lane 0 and displacement 0. Both the opcode wrapper and the helper exponentiated the natural alignment, passing 256 bytes to `wros.checkSpan` for an eight-byte store. The sixth layer converts the width exponent once for all eight lane load and store forms. Bounds and software tag checks cover the actual 1, 2, 4 or 8 bytes, including both granules of a crossing access. [SIMD lane correction](tailcc-simd-lanes.patch)
