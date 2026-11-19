# F# core Wasm development

`wrfs` compiles F# 10 source with Microsoft's F# compiler from .NET SDK 10.0.404. Mono LLVMOnly 10.0.15 compiles the emitted CLI method to LLVM bitcode. The SDK uses the Wasm LLVM producer to generate Wasm32 Core 3.0 and checks the final module before publishing it. The supported applications are freestanding integer kernels and a typed u2rosv2 ABI query. They run as one thread, without a guest CLR, filesystem, sockets or WASI imports.

## Install and build

Choose an immutable SDK commit and registered platform. The development selection installs the F# command, the chosen platform's xmake adapter and the example.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language fsharp --prefix "$PREFIX"
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/unitree/fsharp/development"
python3 "$UWVM_ROS_SDK_ROOT/language/csharp/prepare_host.py" --language fsharp --prefix "$HOST_TOOLS"
export WROS_DOTNET="$HOST_TOOLS/dotnet" WROS_MONO="$HOST_TOOLS/compiler"
export WROS_TOOLCHAIN=/path/to/wasm-llvm
"$UWVM_ROS_SDK_ROOT/bin/wrfs" --dotnet "$WROS_DOTNET" --mono-compiler "$WROS_MONO" \
  --toolchain "$WROS_TOOLCHAIN" --scene-entry Robot.Start \
  "$UWVM_ROS_SDK_ROOT/examples/fsharp/scene-abi/Robot.fs" -o robot.wasm
```

For an offline host install, add `--cache DIR` containing the three Microsoft archives listed in `language/csharp/packages.json`. Installation verifies the archives' lengths and SHA-512 digests, then extracts the selected hosts and reference assemblies and verifies each file's SHA-256. The LLVM producer needs Clang, wasm-ld, llvm-config and the matching development libraries. A host C++ compiler builds the LLVM method extractor.

## Source and compiler options

Use a global F# module, one public integer policy and, for a scene application, an entry calling the policy with `Wros.Scene.Abi()`. The shipped example returns zero for ABI 2. The generated startup function traps on a nonzero result. Grant `uwvm_ros_v2.abi` in the VM to execute this query.

| Option | Effect |
| --- | --- |
| `--entry Module.Method` | Compile an F# function taking one `int` and returning `int`. Export it as `evaluate(i32) -> i32`. |
| `--scene-entry Module.Method` | Compile a `unit -> int` entry which passes the result of `Wros.Scene.Abi()` to a policy function in the same module. |
| `--mte` | Default. Use the WasmMTE producer and prove the final integer kernel has no linear memory, calls or host imports. The checked scene wrapper adds one typed import. |
| `--eh` or `--no-eh` | Enable or disable the standard Wasm EH code-generation feature. The checked kernel cannot use managed exception handling. |
| `--no-mte` | Disable WasmMTE code generation. The same closed-function proof applies. |
| `--host-cxx PATH` | Choose the host C++ compiler for the extractor. |
| `--target wasm32`, `-o FILE.wasm` | Emit a single core Wasm file. Code generation uses `-O3 -g`. |

The method check admits integer locals, arithmetic, comparisons and branches. Managed initialization, heap allocation, arrays, runtime helpers, external side effects, handlers and F# scripts need a different runtime. A failure leaves a previously built output intact. Type checking against FSharp.Core and .NET reference assemblies gives the guest no access to the host APIs in those assemblies.

For xmake, copy `examples/fsharp/scene-abi` into a writable project directory. Keep the four exported environment variables above, then run `xmake f -c -y -a wasm32` and `xmake`. The project selects the F# method with `add_wros_exports("Robot.Start")` and the host query with `add_wros_operations("abi")`. Omitting the operation selects a standalone integer kernel.
