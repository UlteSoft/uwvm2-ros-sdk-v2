# C# AOT validation

The SDK tests compile two C# methods to core wasm32 and execute them in both uwvm2-ros engines. Roslyn produces IL, Mono LLVMOnly produces LLVM bitcode, and the WasmROS LLVM backend produces the guest. The guest imports no host functions. It exercises signed integer arithmetic and the addresses of two simultaneous stack locals, with MTE enabled and explicitly disabled.

The current test covers freestanding methods. A second managed assembly path allocates an array. It compiles to a Wasm object, and the linker reports the dependency on the missing runtime when building the guest. Application projects that use managed objects still require a Wasm-targeted CLR and object-lifetime support in its collector. The installer currently rejects C# development packages.

To reproduce the checks using the pinned .NET compiler inputs, follow the [C# component test instructions](../../tests/csharp/README.md).
