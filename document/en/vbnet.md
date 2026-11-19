# Build a Visual Basic Wasm module

Select the development package by immutable SDK commit. The examples use a Unitree installation. Set `UWVM_ROS_SDK_ROOT` to the directory printed by the installer. Set `WROS_DOTNET`, `WROS_MONO` and `WROS_TOOLCHAIN` to the reviewed .NET SDK, Mono LLVMOnly compiler and LLVM toolchain described in the [managed compiler setup](csharp.md).

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language vbnet --prefix "$PREFIX"
"$UWVM_ROS_SDK_ROOT/bin/wrvb" --dotnet "$WROS_DOTNET" --mono-compiler "$WROS_MONO" \
  --toolchain "$WROS_TOOLCHAIN" --scene-entry Robot.Start \
  "$UWVM_ROS_SDK_ROOT/examples/vbnet/scene-abi/Robot.vb" -o robot.wasm
```

Roslyn compiles the VB source and portable PDB. Mono AOT emits LLVM bitcode. The SDK selects the exact managed method and checks both the IL and the final Wasm instruction stream. A freestanding `--entry Class.Method` exports `evaluate(i32) -> i32`. Use a global, non-generic `NotInheritable Class` without fields or static initialization and a public `Shared Function` taking and returning `Integer`. Bit operations and integer comparisons are supported. Operations that require CLR helpers, including checked overflow handling, are rejected. The default MTE profile proves the admitted leaf has no linear memory access. `--no-mte` keeps this restricted authoring profile. The supported target is single-threaded wasm32 Core 3.0.

The scene example calls `Wros.Scene.Abi()` and passes the result to a checked integer policy in the same class. The final module imports only `uwvm_ros_v2.abi`. To build through Xmake, copy the example directory, run `xmake f -c -y -a wasm32`, then `xmake`. The example specifies its operation, source and method using the common SDK project declarations.
