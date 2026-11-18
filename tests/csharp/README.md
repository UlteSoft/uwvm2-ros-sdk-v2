# C# AOT component regression

This Linux x86-64 regression runs two compiled C# methods in uwvm2-ros. Roslyn emits the managed assembly. Mono LLVMOnly emits its LLVM bitcode. LLVM extracts the two managed entry points and their dependencies. The WasmROS backend applies the selected MTE policy and produces a core wasm32 module with zero host imports.

The numeric method checks 161 signed inputs. The second method takes the addresses of two independent live locals and checks their tags. The test runs the module with the interpreter and AOT, with MTE enabled and disabled. It also compiles a managed array method whose link requires the real Mono runtime. These checks cover freestanding methods. Managed objects, tracing GC, exceptions and application deployment require further tests. C# remains unavailable as a general development package.

## Prerequisites

- A Linux host with the SDK test cgroup, Python 3.11+, GNU C++, the WasmROS LLVM development tools and both uwvm2-ros engines.
- A local .NET SDK 9.0.100-preview.6.24328.19 tree, including Microsoft.NETCore.App.Ref and Microsoft.NETCore.App.Runtime.Mono.wasi-wasm 9.0.0-preview.6.24327.7 installed under its packs directory.
- A native Mono LLVMOnly cross compiler built for core wasm32 with standard Wasm exceptions from dotnet/runtime revision 573461dc897731c11d6166574b77a8c3aabba220, using the Mono LLVM host SDK 16.0.5-alpha.1.24204.1. The SDK1 recipe and its exact source and configuration are in the [pinned build instructions](https://github.com/UlteSoft/uwvm2-ros-sdk/blob/466ec1647ae8577bc2c16bd4f8df8162636817f4/src/language/dotnet/mono-native-eh/README.md).
- An LLVM extractor compatible with the emitted Mono bitcode. Its prefix must contain its matching host runtime libraries under lib and lib/x86_64-unknown-linux-gnu. The SDK LLVM prefix must contain the target Clang, wasm-ld, opt, llvm-config, llvm-objdump and development libraries.

The input lock lists every managed and Mono host file selected for the test. The runner verifies these files and constructs an isolated input directory before executing the compilers. Each run records the other tool hashes, commands, guest hashes, VM results and the cgroup limits. A different host compiler build requires review before updating its digest.

## Run

Start in the SDK repository. Set WROS_DOTNET to the SDK tree, WROS_MONO to the compiler prefix containing bin/mono-aot-cross and lib, LLVM_EXTRACT to the extractor executable, WROS_TOOLCHAIN to the WasmROS LLVM prefix, and WROS_VM to the VM executable. The output directory must be new.

    /usr/bin/python3 ../uwvm2-ros/tools/ros_scene/in_existing_cgroup.py \
      /usr/bin/taskset -c 4-7 /usr/bin/flock "$PWD/.tmp/sdk-qualification.lock" \
      /usr/bin/python3 -B tests/csharp_aot.py \
      --dotnet "$WROS_DOTNET" --mono-compiler "$WROS_MONO" \
      --extract "$LLVM_EXTRACT" --toolchain "$WROS_TOOLCHAIN" --runtime "$WROS_VM" \
      --output "$PWD/.tmp/csharp-methods"

Open results.json in the output directory for the observed commands and statuses. The array link receives the expected unresolved Mono runtime symbol and contributes a passing negative case.
