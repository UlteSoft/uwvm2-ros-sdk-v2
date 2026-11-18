# Flang compiler and guest numerical runtime

The intrinsic modules, numerical runtime sources and their transitive LLVM headers come from the SDK's vendored LLVM 23.1.5 source archive, revision `392dfff97d29b59d77e5cac6d4b6ef2585fe7117`. The license is reproduced in [LICENSE.TXT](LICENSE.TXT). The selected source files keep their upstream notices. The source archive is shared with the C compiler under `third-parties/sources/`.

The maintained [WebAssembly target ABI patch](llvm23-wasm-abi.patch) supplies the single-result C calling convention in Flang and target pointer-width definitions for its intrinsic modules. The retained `iso_c_binding.f90` also sets `c_int_fast16_t` to the 32-bit kind used by the WASI libc headers for both memory widths. The [address-kind patch](llvm23-flang-wasm32-address-kind.patch) gives LOC, MALLOC and SIZEOF the wasm32 pointer result kind. C_SIZE_T and C_INTPTR_T inherit this kind from SIZEOF. Each compilation generates the module interfaces for the requested address width.

The SDK compiles `numeric.cpp` and `complex-powi.cpp` from source with its selected Wasm compiler and sysroot. These supply scalar numerical functions and complex integer powers. The SDK builds the small guest startup and permission-sensitive ROS import wrappers locally.

For Wasm/WASI, the retained numerical runtime routes its fatal arithmetic diagnostic to a guest trap. The upstream stderr formatting path would acquire file-descriptor imports, including at program shutdown.

Flang's runtime model can express descriptor bounds as signed 64-bit values when a 64-bit host targets wasm32. The IR adapter selects a guest bridge for that signature. The runtime checks occupied bounds against the guest descriptor width before narrowing them, and preserves an invalid extent for allocation status handling. Empty intervals retain extent zero.

For descriptor-based array operations, the SDK also retains the upstream allocation, assignment, copy, derived-type, work-queue, type-information, pointer and ISO C interoperability sources. Its WebAssembly build uses the upstream compute work-queue variant. It omits the FILE-based descriptor dump procedures and uses guest-local runtime defaults. The SDK checks array extents, byte-stride multiplication and the pointer-validation footer size before an allocation. The normal Fortran status and error-message paths remain available for recoverable failures. See [the guest runtime adapter](../../language/fortran/compute_platform.cpp) and [the executable descriptor regression](../../tests/fortran_descriptors.py).

The array runtime includes the upstream `sum`, `reduction`, `transformational`, integer/real `dot-product` and integer/real `matmul` translation units and their shared headers. The SDK compiles the units referenced by the input objects for the selected Wasm profile. These additional files retain the upstream license.

The [standalone build patch](llvm23-globals-intrinsic-header.patch) includes the complete LLVM intrinsic instruction type in the WebAssembly globals pass when precompiled headers are disabled.

The [assumed-size extent patch](llvm23-flang-assumed-size-index.patch) emits the negative-one extent marker at the target index width. This keeps LLVM debug intrinsics valid for legacy assumed-size dummy arrays in wasm32 and wasm64 code.
