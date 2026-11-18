# C# AOT validation

The SDK tests compile two C# methods to core wasm32 and execute them in both uwvm2-ros engines. Roslyn produces IL, Mono LLVMOnly produces LLVM bitcode, and the WasmROS LLVM backend produces the guest. The guest imports no host functions. It exercises signed integer arithmetic and the addresses of two simultaneous stack locals, with MTE enabled and explicitly disabled.

The current test covers freestanding methods. A second managed assembly path allocates an array. It compiles to a Wasm object, and the linker reports the dependency on the missing runtime when building the guest. Application projects that use managed objects still require a Wasm-targeted CLR and object-lifetime support in its collector. The installer currently rejects C# development packages.

To reproduce the checks using the pinned .NET compiler inputs, follow the [C# component test instructions](../../tests/csharp/README.md).

## Mono page allocation under a memory limit

The repository also includes the Microsoft Mono WASI page manager and its source dependencies. This regression needs CMake, patch, a WasmROS LLVM compiler, its matching wasm32/EH/MTE sysroot receipt, and a two-engine VM. From the SDK repository, run the following command with a new output directory.

    /usr/bin/python3 ../uwvm2-ros/tools/ros_scene/in_existing_cgroup.py \
      /usr/bin/taskset -c 4-7 /usr/bin/flock "$PWD/.tmp/sdk-qualification.lock" \
      /usr/bin/python3 -B tests/csharp_mono_pages.py \
      --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --runtime "$WROS_VM" \
      --output "$PWD/.tmp/mono-pages"

The test checks adjacent tagged allocations, a payload copy, owner retirement, partial page release and zeroing on reuse. It runs with VM tag checks on and off. Two additional modules have fixed memory limits. A module capped at four pages returns allocation failure. A module with two additional pages can fulfill a one-page request after a preferred larger batch fails. Fatal diagnostics trap the test, and each guest has zero host imports. The fixture explicitly allocates the test objects. Managed collection and relocation still require qualification in the full CLR.

## Compile a C# numeric method with wrcs

Select `--component numeric-aot` after the installer's `--` separator with the language `csharp`. The selection installs `bin/wrcs`, the numeric admission and LLVM sources, the platform and C# Xmake adapters, and a complete example. The compiler host needs the .NET SDK, WASI Mono cross compiler and WasmROS LLVM development prefix listed above. Pin them in `WROS_DOTNET`, `WROS_MONO` and `WROS_TOOLCHAIN`. GNU C++ builds a host-side bitcode reader. Every successful application output is a core wasm32 module.

Install from the exact SDK commit with the stable bootstrap and choose a local output prefix.

```sh
/usr/bin/python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree \
  --language csharp --prefix "$SDK_PREFIX" -- --component numeric-aot
export UWVM_ROS_SDK_ROOT="$SDK_PREFIX/$SDK_COMMIT/unitree/csharp/numeric-aot"
```

The host inputs are .NET SDK 9.0.100-preview.6.24328.19, the Microsoft.NETCore.App.Ref and Mono WASI packs at 9.0.0-preview.6.24327.7, and the LLVMOnly cross compiler built from dotnet/runtime commit `573461dc897731c11d6166574b77a8c3aabba220`. The component stages exactly the files listed in `language/csharp/inputs.sha256` and checks every digest. The SDK1 repository documents how to build that pinned cross compiler. [Mono toolchain instructions](https://github.com/UlteSoft/uwvm2-ros-sdk/blob/466ec1647ae8577bc2c16bd4f8df8162636817f4/src/language/dotnet/mono-native-eh/README.md)

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrcs" --dotnet "$WROS_DOTNET" --mono-compiler "$WROS_MONO" \
  --toolchain "$WROS_TOOLCHAIN" --entry Filter.Scale --legacy-mte \
  "$UWVM_ROS_SDK_ROOT/examples/csharp/numeric-aot/Filter.cs" -o filter.wasm
```

Declare the entry in a global, non-generic static class with the signature `public static int Scale(int input)`. Select it by `Class.Method`. The exported Wasm signature is `evaluate(i32) -> i32`. The module has one 64 KiB memory and accepts zero host imports. Supported method bodies use integer constants, arguments, locals, comparisons, bit operations, unchecked addition, subtraction and multiplication, and branches. A metadata reader checks the method's actual IL before AOT. The compiler uses its MethodDef row to retrieve the corresponding Mono function. It checks the hidden context is unused and emits the one-argument ABI. Assemblies containing type or module initializers, and entries requiring arrays, objects, helpers, exceptions or P/Invoke, require a broader CLR profile and are rejected. Independent methods outside the selected entry have no guest entry points.

`--legacy-mte` explicitly enables unsigned instrumented code generation. `--no-mte` explicitly selects plain output. Default strict MTE builds require a signed release. C# currently has no such release. For Xmake, start from `examples/csharp/numeric-aot/xmake.lua`, set `set_language("csharp")` and use `add_wros_exports("Filter.Scale")` to choose the managed member. The target builds at `-O3 -g`. Calling `evaluate` requires an embedding that supplies its integer argument. Platform selection makes no driver grants.

Roslyn emits a Portable PDB and hashes each document with SHA-256. The AOT frontend matches the method’s first visible sequence point to an input source digest and records its C# name, the source basename and that line in DWARF. A method with exactly one visible sequence point also gets statement-level instruction mapping. Methods with multiple sequence points carry method-level location only. A hidden or unmatched source contributes no line mapping. Debug data omits absolute build-host source paths.

The repository includes `tests/csharp_source_locations.py` for a single statement, a loop and a remapped source name. Run `tests/csharp_numeric_performance.py --help` to compare a compiled Filter.Scale module with the out-of-line native C implementation. The timing harness calls the separate Wasm library, checks the complete arithmetic sum, and records paired wall-time slopes on core 4. VTune collects hardware Hotspots and Microarchitecture Exploration for both workloads and records whether the requested sampling interval and source/assembly mapping succeeded.
