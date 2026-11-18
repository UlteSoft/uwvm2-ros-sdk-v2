# Flang compiler and guest numerical runtime

The intrinsic modules, numerical runtime sources and their transitive LLVM headers come from the SDK's vendored LLVM 23.1.5 source archive, revision `392dfff97d29b59d77e5cac6d4b6ef2585fe7117`. The license is reproduced in [LICENSE.TXT](LICENSE.TXT). The selected source files keep their upstream notices. The source archive is shared with the C compiler under `third-parties/sources/`.

The maintained [WebAssembly target ABI patch](llvm23-wasm-abi.patch) supplies the single-result C calling convention in Flang and target pointer-width definitions for its intrinsic modules. The retained `iso_c_binding.f90` also sets `c_int_fast16_t` to the 32-bit kind used by the WASI libc headers for both memory widths. Each compilation generates the module interfaces for the requested address width.

The SDK compiles `numeric.cpp` and `complex-powi.cpp` from source with its selected Wasm compiler and sysroot. These supply scalar numerical functions and complex integer powers. The SDK builds the small guest startup and permission-sensitive ROS import wrappers locally.

For Wasm/WASI, the retained numerical runtime routes its fatal arithmetic diagnostic to a guest trap. The upstream stderr formatting path would acquire file-descriptor imports, including at program shutdown.

For descriptor-based array operations, the SDK also retains the upstream allocation, assignment, copy, derived-type, work-queue, type-information, pointer and ISO C interoperability sources. Its WebAssembly build uses the upstream compute work-queue variant. It omits the FILE-based descriptor dump procedures and uses guest-local runtime defaults. The SDK checks array extents, byte-stride multiplication and the pointer-validation footer size before an allocation. The normal Fortran status and error-message paths remain available for recoverable failures. See [the guest runtime adapter](../../language/fortran/compute_platform.cpp) and [the executable descriptor regression](../../tests/fortran_descriptors.py).
