# C guest projects

Install `--language c`. From a copy of `examples/c`, run `xmake build` and `xmake test -j1` with the environment described in the [installation guide](../install-xmake.md).

`<uwrosv2/scene.h>` exposes the C scene API. `uwrosv2_abi()` calls the version import. To use a provisioned resource, open its capability using the configured alias, check each returned status, and close the resource and capability when finished. The generated domain headers declare the corresponding handles and buffers.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrc" --reactor --export _start --std c17 main.c -o guest.wasm
```

`wrc` is an LLVM executable with an embedded compiler. The matched linker, archiver and Wasm sysroot are installed with it. The `--reactor --export _start` pair links guest sources with their own `_start`. The C migration project at `examples/c/migration/zlib` exercises an existing C library with the SDK.

The driver searches the installed C bindings and the selected platform's C headers automatically. The WASIp1 C library headers are available for inspection in `include/sysroot/c/`. Include them by their standard names, such as `<stdio.h>`. A C++ project can include the C bindings from this selection. All C entry points then carry `throw()` in C++98/03 and `noexcept` from C++11 onward.

## WasmMTE pointer subtraction

In C, C++, Objective-C and Objective-C++, subtracting pointers into the same array gives a signed distance in elements. For example, two pointers to 12-byte structures that are 60 bytes apart differ by five elements. With `--mte`, Clang emits `memtag.sub` for data pointers in linear memory 0 before dividing by the element size. With `--no-mte`, Clang uses ordinary pointer subtraction. Subtracting two `uintptr_t` values always uses the full unsigned integer width, including when the values came from pointer casts.

An MTE translation unit can select the byte-level operation explicitly. The signatures below use `ptrdiff_t` from `<stddef.h>` and `uintptr_t` from `<stdint.h>`.

```c
ptrdiff_t __builtin_wasm_memtag_sub(int memory, void *lhs, void *rhs);
uintptr_t __builtin_wasm_memtag_sub_raw(const void *lhs, const void *rhs);
ptrdiff_t __builtin_wasm_memtag_sub_uintptr(int memory, uintptr_t lhs, uintptr_t rhs);
```

- `__builtin_wasm_memtag_sub` takes pointers and returns the signed byte difference of their linear addresses. Use the constant memory index `0` for the SDK's primary memory.
- `__builtin_wasm_memtag_sub_raw` subtracts the complete pointer representations, including the tag bits, and returns the byte difference modulo 2³² on wasm32 or 2⁶⁴ on wasm64.
- `__builtin_wasm_memtag_sub_uintptr` interprets both integer operands as encoded pointers and applies `memtag.sub` for the given memory. The result is a signed byte difference, 32 bits on wasm32 and 64 bits on wasm64. A `uint32_t` argument zero-extends on wasm64. A `uintptr_t` on that ABI preserves all 64 input bits. Cast a signed 32-bit value to `uint32_t` first when its bits represent an unsigned offset.

Clang diagnoses a nonconstant memory index. With `--no-mte`, `__has_builtin` returns `0` for every `__builtin_wasm_memtag_*` name, and direct use is diagnosed as an unknown builtin or undeclared identifier. In an MTE translation unit, `no_sanitize("memtag")` and `disable_sanitizer_instrumentation` suppress the automatic lowering within the annotated function. Explicit builtin calls still select their named operation.
