# C# AOT validation

Install the pinned Microsoft .NET SDK 10.0.404 compiler files and the 10.0.15 Mono WASI packs with `python3 language/csharp/prepare_host.py --prefix /path/to/managed-tools`. An offline installation accepts `--cache DIR` containing the three official archives named in `language/csharp/packages.json`. Set `WROS_DOTNET` to the installed `dotnet` directory and `WROS_MONO` to its sibling `compiler` directory.

The standalone numeric regression compiles two C# methods to core wasm32 and execute them in both uwvm2-ros engines. Roslyn produces IL, Mono LLVMOnly produces LLVM bitcode, and the WasmROS LLVM backend produces the guest. The guest imports no host functions. It exercises signed integer arithmetic and the addresses of two simultaneous stack locals, with MTE enabled and explicitly disabled.

The current test covers freestanding methods. A second managed assembly path allocates an array. It compiles to a Wasm object, and the linker reports the dependency on the missing runtime when building the guest. Application projects that use managed objects still require a Wasm-targeted CLR and object-lifetime support in its collector. The default C# development package installs the scalar compiler described below.

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

Select the language `csharp` to install the freestanding integer development profile. The explicit `--component numeric-aot` selection is also available. The selection installs `bin/wrcs`, the numeric admission and LLVM sources, the platform and C# Xmake adapters, and a complete example. The compiler host needs the .NET SDK, WASI Mono cross compiler and WasmROS LLVM development prefix listed above. Pin them in `WROS_DOTNET`, `WROS_MONO` and `WROS_TOOLCHAIN`. GNU C++ builds a host-side bitcode reader. Every successful application output is a core wasm32 module.

Install from the exact SDK commit with the stable bootstrap and choose a local output prefix.

```sh
/usr/bin/python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree \
  --language csharp --prefix "$SDK_PREFIX"
export UWVM_ROS_SDK_ROOT="$SDK_PREFIX/$SDK_COMMIT/unitree/csharp/development"
```

The official Mono LLVMOnly cross compiler comes from Microsoft.NETCore.App.Runtime.AOT.linux-x64.Cross.wasi-wasm 10.0.15. The component checks each compiler, host runtime and reference assembly against the SDK input lock.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrcs" --dotnet "$WROS_DOTNET" --mono-compiler "$WROS_MONO" \
  --toolchain "$WROS_TOOLCHAIN" --entry Filter.Scale \
  "$UWVM_ROS_SDK_ROOT/examples/csharp/numeric-aot/Filter.cs" -o filter.wasm
```

Declare the entry in a global, non-generic static class with the signature `public static int Scale(int input)`. Select it by `Class.Method`. The exported Wasm signature is `evaluate(i32) -> i32`. The kernel accepts zero host imports. Supported method bodies use integer constants, arguments, locals, comparisons, bit operations, unchecked addition, subtraction and multiplication, and branches. A metadata reader checks the method's actual IL before AOT. The compiler uses its MethodDef row to retrieve the corresponding Mono function. It checks the hidden context is unused and emits the one-argument ABI. Assemblies containing type or module initializers, and entries requiring arrays, objects, helpers, exceptions or P/Invoke, require a broader CLR profile and are rejected. Independent methods outside the selected entry have no guest entry points.

The default and `--mte` compile with WasmMTE enabled. Before publishing a standalone kernel, `wrcs` decodes the final Wasm, checks every instruction in its only function against a register-only integer profile, and removes the unused private memory. The resulting module has no linear memory, globals, imports or other executable entries. Code that takes a local address can require memory and fail this proof. A relocatable object also requires a subsequent link, so it cannot use this per-module proof. Explicit `--legacy-mte` generates unsigned instrumented code and `--no-mte` opts out of tagging. Both explicit modes retain the private 64 KiB memory. These profiles do not qualify a general CLR heap. For Xmake, start from `examples/csharp/numeric-aot/xmake.lua`, set `set_language("csharp")` and use `add_wros_exports("Filter.Scale")` to choose the managed member. The target builds at `-O3 -g`. Calling `evaluate` requires an embedding that supplies its integer argument. Platform selection makes no driver grants.

Roslyn emits a Portable PDB and hashes each document with SHA-256. The AOT frontend matches the method’s first visible sequence point to an input source digest and records its C# name, the source basename and that line in DWARF. A method with exactly one visible sequence point also gets statement-level instruction mapping. Methods with multiple sequence points carry method-level location only. A hidden or unmatched source contributes no line mapping. Debug data omits absolute build-host source paths.

The repository includes `tests/csharp_source_locations.py` for a single statement, a loop and a remapped source name. Run `tests/csharp_numeric_performance.py --help` to compare a compiled Filter.Scale module with the out-of-line native C implementation. The timing harness calls the separate Wasm library, checks the complete arithmetic sum, and records paired wall-time slopes on core 4. VTune collects hardware Hotspots and Microarchitecture Exploration for both workloads and records whether the requested sampling interval and source/assembly mapping succeeded.

### Link a numeric kernel into a robot body

For a controller and numeric kernel in the same trust domain, add `-c --sysroots "$WROS_SYSROOTS"` to the compiler invocation and select a `.o` output. The result is a relocatable core-Wasm object with the C ABI `int evaluate(int)`. The frontend checks that the kernel can link with zero guest imports and binds the object to the compiler, sysroot and guest profile. The legacy MTE selection produces an unsigned object. A strict release build requires a reviewed object. The SDK C or C++ frontend checks the final body's imports. Linked code shares the body's memory and grants.

For Xmake, declare the C# kernel with `set_kind("static")`, `add_wros_exports("Filter.Scale")` and a matching `WROS_SYSROOTS`. A C body can select its separately installed C SDK with `set_wros_sdk` and use `add_deps` for that archive. Both SDK selections must come from the same commit. The repository's `tests/csharp_numeric.py --sysroots` exercises the linked artifact in both VM engines. `tests/mujoco_guest.py --language csharp` uses a C# scalar calculation in a C body which owns the authorized simulation connection.

### Run a C# program that queries the ROS scene ABI

Copy `examples/csharp/scene-abi` or invoke `wrcs --scene-entry Robot.Start` with the same host tool flags as the scalar compiler. The SDK supplies the `Wros.Scene.Abi()` reference used by Roslyn. The parameterless public static entry must return the result of passing this query to a public static integer policy in the same class. The SDK verifies both managed call targets from the IL and runs the policy through Mono LLVMOnly. Returning zero from the policy completes startup. A nonzero result traps the guest. Xmake selects this entry with `add_wros_exports("Robot.Start")` and `add_wros_operations("abi")`.

The final module exports only `_start`. It has no linear memory and its sole import is `uwvm_ros_v2.abi() -> i32`. The VM must bind the main module to a scene and expose the ABI query. A hidden interface prevents the guest from starting. Additional CLR calls or host operations fail compilation.

## Scoped driver connection

Use `wrcs --driver-entry Driver.Start` to lower an entry that returns the local integer policy applied to `Wros.Scene.DriverConnectionStatus("arm")`. A literal alias is required. Select the same binding in Xmake with `add_wros_operations("driver.connect")`. The guest uses one private page and four typed imports for the capability and connection lifetime. The parent driver permission and the platform child both apply. [Driver binding and verification](managed-platform-examples.md).
