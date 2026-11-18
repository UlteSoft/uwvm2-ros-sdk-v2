# Developing a Fortran Wasm application

`bin/wrfortran` compiles a Fortran `PROGRAM` to a Wasm executable. It supports fixed-form and free-form input, ordered Fortran modules, ISO C interoperability and the numerical procedures linked from the vendored Flang runtime. The program starts at `_start` in its own guest memory. This profile currently lacks the general Flang external I/O, coarray and descriptor-based runtime libraries.

## Prepare the host tools

Use an SDK code generator with WasmMTE support and a matching sysroot build receipt. The host bootstrap prefix below contains native Clang, Clang++ and LLD. The SDK prefix contains its Wasm compiler, linker, `llvm-config`, development headers and static LLVM libraries. From the SDK root, run:

```sh
python3 language/fortran/build_flang.py \
  --bootstrap "$BOOTSTRAP" --source-work "$LLVM_CACHE" --work "$FLANG_BUILD" \
  --output "$WROS_TOOLCHAIN/bin/flang"
python3 language/fortran/prepare.py \
  --toolchain "$WROS_TOOLCHAIN" --host-cxx /usr/bin/g++
```

The source recipe configures LLVM's WebAssembly backend, then checks both guest widths and verifies that the built compiler rejects native x86 object generation before installation. It writes a host-tool receipt beside the executable. The IR helper records its source, executable and SDK code-generator digests. Toolchain preparation requires a trusted local builder. Building these host tools is separate from compiling a guest.

## Compile a program

```fortran
program application
  use wros_scene, only: wr_abi
  implicit none
  integer :: version
  version = wr_abi()
end program
```

```sh
bin/wrfortran --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" \
  --target wasm32 -O3 -g application.f90 -o application.wasm
```

`wros_scene` derives its interfaces from the installed ROSv2 ABI. Each `wr_` function uses explicit value arguments of the specified Wasm integer widths. The output above imports `uwvm_ros_v2.abi`. The deploying VM must expose that interface to this module. An SDK import declaration never grants VM authority.

| Option | Effect |
| --- | --- |
| `--toolchain DIR` | Select the explicit Wasm compiler, linker and LLVM tools. |
| `--sysroots FILE` | Add a build receipt. Exactly one closure must match this compiler and guest profile. |
| `--target wasm32` or `wasm64` | Select the guest pointer width. The default is wasm32. |
| `--core 3.0` or `mvp` | Select the core instruction profile. The default is 3.0. |
| `--eh`, `--no-eh` | Select the matching exception ABI. Core 3.0 defaults to EH. |
| `--mte`, `--no-mte` | Select whole-target memory tagging, enabled by default. Objects, archive members and the sysroot must agree. |
| `-pthread`, `--threads` | Request a threaded closure. Each requested configuration requires a matching supplied sysroot. |
| `-O0…-O3`, `-Os`, `-Oz`, `-g` | Select code generation and optional debug information. The default optimization is `-O3`. |
| `--link-object FILE` | Add an SDK-produced Wasm relocatable object or static archive. Repeat for each input. |
| `--flang FILE`, `--mte-tool FILE` | Select exact host tools. Qualification also accepts one explicitly pinned development build of Flang. |
| `SOURCE… -o FILE` | Compile input files in module dependency order and publish the audited Wasm. |

Stack or global accesses can be optimized according to the selected target and the compiler's proofs. Flang 23 has no dedicated Fortran source directive for WasmMTE. The SDK preserves sanitizer attributes and metadata already present in IR. The included C/C++ runtime uses the same target profile.

Qualification executes the program under the VM interpreter and AOT engine. It verifies an actual ROS import allow/deny pair, an escaping array, an in/out scalar, ISO C widths, and an upstream numerical runtime call. The test reads the disassembly of the final Fortran function. For the commands and fixture, see [the executable qualification](../../tests/fortran_aot.py) and [Fortran source](../../tests/fortran/body.f90).
