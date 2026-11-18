# Developing a Fortran Wasm application

`bin/wrf` compiles a Fortran `PROGRAM` to a Wasm executable. It supports fixed-form and free-form input, ordered Fortran modules, ISO C interoperability and the numerical procedures linked from the vendored Flang runtime. The program starts at `_start` in its own guest memory. Its compute runtime supports allocatable arrays, pointer allocation and ISO C descriptors. General external Fortran I/O and coarray programs still require additional runtime support.

## Prepare the host tools

For an existing reviewed toolchain and sysroot, the ordinary development package suffices. To build the tools themselves, select the compiler sources for the same SDK commit. The installer reports the path containing the language frontend and shared source recipes.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language fortran \
  --prefix "$PREFIX" -- --component compiler-source
```

Use an SDK code generator with WasmMTE support and a matching sysroot build receipt. The host bootstrap prefix below contains native Clang, Clang++ and LLD. The SDK prefix contains its Wasm compiler, linker, `llvm-config`, development headers and static LLVM libraries. From the SDK root, run:

```sh
python3 language/fortran/build_flang.py \
  --bootstrap "$BOOTSTRAP" --source-work "$LLVM_CACHE" --work "$FLANG_BUILD" \
  --output "$WROS_TOOLCHAIN/bin/flang"
python3 language/fortran/prepare.py \
  --toolchain "$WROS_TOOLCHAIN" --host-cxx /usr/bin/g++
```

The source recipe configures LLVM's WebAssembly backend, then checks both guest widths and verifies that the built compiler rejects native x86 object generation before installation. It writes a host-tool receipt beside the executable. The IR helper records its source, executable and SDK code-generator digests. Toolchain preparation requires a trusted local builder. Building these host tools is separate from compiling a guest.

The Flang receipt binds the upstream archive, ordered code generator patches and the Flang build patches. Assumed-size arrays retain full variable debug information with the index width of the selected Wasm target. The address-sized intrinsics LOC, MALLOC and SIZEOF use the pointer width of the selected target. This also sets ISO_C_BINDING’s C_SIZE_T and C_INTPTR_T to four bytes on wasm32 and eight on wasm64. The compiler and its debug information use target-width C descriptor fields for the element size, lower bounds, extents and byte strides. The final link rejects inconsistent procedure signatures. The standalone build includes the full LLVM intrinsic type declaration when compiling without precompiled headers.

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
bin/wrf --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" \
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
| `--flang FILE`, `--mte-tool FILE` | Select exact host tools. Flang must match the receipt for the WebAssembly-only build. |
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

## Qualify a local compiler release

The default MTE mode requires a locally trusted, signed release for the requested guest profile. From a clean SDK source checkout, run the shared qualification recipe with `--language fortran --target wasm32 --eh -O3 -g` (or select a measured wasm64 closure). Supply the approved hashes of `TOOLCHAIN/bin/flang` and `TOOLCHAIN/bin/wros-flang-mte` with `--approved-flang-sha256` and `--approved-marker-sha256`, alongside the approved SDK commit, backend, VM and sysroot digests. Omit `-g` to qualify the frontend’s ordinary default. Debug and non-debug builds have distinct release rows. The recipe runs both guest engines, checks Fortran storage operations, and verifies that Flang accepts both Wasm widths and rejects native object emission. The explicit development Flang does not satisfy release qualification.

Generate C and C++ release rows for the same VM, compiler, sysroot, `-O3 -g` and EH profile. The Fortran frontend uses those frontends for its language runtime and ROS import adapters. Bundle all three rows and sign the bundle using your local release authority. Production development installs require the signed bundle and trust configuration. [Shared release procedure](../../tools/wasm/memtag/README.md) · [Qualification command](../../tools/wasm/memtag/qualify_local_c.py) · [Signed installation test](../../tests/local_release_wsea.py)

## Array intrinsics

The frontend inspects unresolved symbols in the program and its sealed object and archive inputs. When a program calls array intrinsics, it compiles the corresponding Flang guest procedures with the selected pointer width, exception ABI and memory-tagging mode. This includes real and integer dot products, real, integer and logical matrix products, masked and dimensioned sums, logical reductions and array reshaping. An application that needs only scalar arithmetic omits these translation units.

The regression multiplies two real matrices and two integer matrices, computes column and masked reductions, and checks a logical matrix product. It checks the linked Fortran function names, runs the guest under both VM engines, and inspects its sole host import, `uwvm_ros_v2.abi`. Complex matrix multiplication and external Fortran I/O require additional runtime components. [Fortran example](../../tests/fortran/array_intrinsics.f90) · [Regression](../../tests/fortran_intrinsics.py)

## Building a Fortran static library

Use `wrf --static` to compile Fortran procedure definitions into a guest archive. The frontend seals each Wasm object with its target profile, compiler and sysroot identity. The final application supplies the Fortran runtime routines referenced by the library. A library has no deployment entry point. This example uses a procedure with a declared C binding. Traditional external Fortran procedures also work. Keep source units sharing a Fortran `USE` interface in the same target in module dependency order.

```sh
wrf --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --static kernel.f90 -o filter.a
wrf --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --link-object filter.a body.f90 -o robot.wasm
```

In Xmake, give the library target `set_kind("static")` and add it to the executable using `add_deps`. Both targets select the same SDK commit, width, exception mode and MTE configuration. [Two-target project](../../examples/fortran/static/xmake.lua)

The archive regression can also use the original LAPACK norm procedure shipped with the Lite3 SDK and the division procedure shipped with the ROS Taskflow release. Supply their paths through `--dlapy3` and `--dladiv`. The test checks the exact source digests and evaluates the numerical results in both VM engines. [Archive regression](../../tests/fortran_archives.py)

## Reading clocks

Fortran `SYSTEM_CLOCK` reads the WASIp1 monotonic clock. `CPU_TIME` reads the VM process CPU clock. The frontend links the clock adapter when a guest object or static archive references these intrinsics. Both use the single read-only `clock_time_get` import, spelled `clock_time_get_wasm64` in a wasm64 module. The deployment supplies the interface and grants each clock ID separately. Process CPU time includes work performed by other modules in the same VM process.

With monotonic clock access, a 32-bit count advances in milliseconds and a 64-bit count in nanoseconds. If the query fails, `COUNT` receives `-HUGE(COUNT)`, and `COUNT_RATE` and `COUNT_MAX` receive zero. A failed CPU-time query returns a negative value. Each read checks current authority. For simulated or externally controlled ROS time, use the `wr_clock_read` binding with its ROSv2 clock capability. [Clock regression](../../tests/fortran_clocks.py)
