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
