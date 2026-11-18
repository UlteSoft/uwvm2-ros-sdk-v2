# Developing a Fortran Wasm application

`bin/wrfortran` compiles a Fortran `PROGRAM` to a Wasm executable. It supports fixed-form and free-form input, ordered Fortran modules, ISO C interoperability and the numerical procedures linked from the vendored Flang runtime. The program starts at `_start` in its own guest memory. Its compute runtime supports allocatable arrays, pointer allocation and ISO C descriptors. General external Fortran I/O and coarray programs still require additional runtime support.

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

Pass a buffer address to an i64 ROS import with `wr_address(c_loc(buffer))` from `wros_scene`. Declare the buffer as `target` and obtain `c_loc` from `iso_c_binding`. This conversion preserves every pointer tag bit and zero-extends a wasm32 address to 64 bits. A signed integer cast can incorrectly extend bit 31 into the upper half. On wasm64, the helper preserves all 64 bits.

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

Stack or global accesses can be optimized according to the selected target and the compiler's proofs. Flang 23 has no dedicated Fortran source directive for WasmMTE. The SDK preserves sanitizer attributes and metadata already present in IR. The included C/C++ runtime uses the same target profile. The managed-stack producer promotes register-only values and registers fixed linear stack ranges with the VM. A bound on one subscript can prove that access safe while the underlying object still needs a distinct tag from its physical neighbors. The current producer requires statically bounded stack allocation and a matching release on each supported exit. Dynamic stack arrays and non-local exits that it cannot match produce a compilation diagnostic. A no-EH build can compile a bounded numerical callee that passes its results back to C. When a Fortran procedure keeps a linear stack object across an external call whose unwind behavior is unknown, strict no-EH compilation rejects it. In the EH profile the compiler releases that frame’s objects before rethrowing an escaping exception.

Qualification executes the program under the VM interpreter and AOT engine. It verifies an actual ROS import allow/deny pair, an escaping array, an in/out scalar, ISO C widths, and an upstream numerical runtime call. The test reads the disassembly of the final Fortran function. For the commands and fixture, see [the executable qualification](../../tests/fortran_aot.py) and [Fortran source](../../tests/fortran/body.f90).

The cross-language stack test builds a sealed C inspection object and links it into an actual Fortran program. The program uses ISO C binding to record two live array addresses as integers. C compares their physical separation and tags, and checks the result of a legal read from each array. The fixture requires a 16-byte separation. It runs on wasm32 and wasm64 with both VM engines and with runtime tagging enabled and disabled. Supply a tagged sysroot manifest for each width under test. The default suite checks wasm32 and wasm64 with the no-EH ABI. Use `--address-width 32 --exception-model eh` for a wasm32 EH sysroot. The output directory must be new. [Test command and accepted options](../../tests/fortran_stack_neighbors.py)

Use `--storage static-and-heap` with the same test and a matching EH sysroot to check Fortran module variables and two independent `ALLOCATABLE` arrays. The program obtains its array length from the authorized ROS ABI query. It allocates and fills both arrays, passes their addresses to C while they are live, and deallocates them in Fortran. The C check uses the allocator's actual capacity to measure the physical gap between ranges and reads shadow metadata after deallocation. This fixture exercises element-wise assignment and allocation without a `STAT=` specifier. The separate descriptor application below exercises whole-array assignment and allocation with status reporting. [Application](../../tests/fortran/storage_neighbors.f90) · [Storage checks](../../tests/fortran/storage_neighbors.c)

## Building with xmake

Install the language and platform at the same commit and select the returned development directory. For example, the following command requests the Unitree package and the Fortran frontend.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language fortran --prefix "$PREFIX"
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/unitree/fortran/development"
```

With `WROS_TOOLCHAIN` and `WROS_SYSROOTS` set, place this project file alongside `application.f90` and run `xmake f -p wasm-wasip1 -a wasm32` followed by `xmake robot`.

```lua
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("robot")
    set_kind("binary")
    set_language("fortran")
    set_ros_platform("unitree")
    set_wros_profile({core = "3.0", mte = true, eh = true})
    set_optimize("fastest")
    set_symbols("debug")
    add_files("application.f90")
target_end()
```

List multiple Fortran source files in module dependency order. The installed [complete project](../../examples/fortran/xmake.lua) builds [an array-processing application](../../examples/fortran/body.f90). The adapter accepts a checked C or C++ static archive through `add_deps`. To run the example that calls `wr_abi()`, expose its query when launching the VM. The [xmake reference](xmake.md) lists environment variables, profile controls and local execution options.

## Arrays and C descriptors

Fortran applications can use `ALLOCATE(..., STAT=rc, ERRMSG=msg)`, `MOVE_ALLOC`, whole-array assignment and `DEALLOCATE(..., STAT=rc)`. The frontend selects the vendored Flang descriptor procedures when its input objects reference them. It compiles these procedures for the application's address width, exception mode and MTE setting. The numeric and descriptor libraries use the same sealed guest object format as the application. The array library requires no guest file descriptors, network socket or environment access.

The runtime checks allocation bounds, byte strides and the size of the deallocation footer against the target's signed pointer range before allocating. An unrepresentable allocation with `STAT=` returns a failure code. A zero-size allocation produces an allocated array with zero elements. With the C interoperability header, compile C callers with `-I "$UWVM_ROS_SDK_ROOT/third-parties/fortran/flang/include"` and include `"flang/ISO_Fortran_binding.h"`.

The descriptor regression checks a Fortran pointer alias, successful and failed allocations, a status message, moved ownership, zero extents, whole-array assignment and an independently established rank-two C descriptor. The resulting application imports only `uwvm_ros_v2.abi`. [Test driver](../../tests/fortran_descriptors.py) · [Fortran application](../../tests/fortran/descriptor_status.f90) · [C caller](../../tests/fortran/descriptor_status.c)
