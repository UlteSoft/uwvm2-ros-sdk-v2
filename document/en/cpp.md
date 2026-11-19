# C++ development with wrcc

The C++ frontend uses a Wasm-only build of the official LLVM 23.1.5 release with the Herbceptions language and ABI backport. A function can declare its failure type with `return_failure{E}`. At the call site, `catch return_failure(expression)` exposes the success value or the typed error. Normal scope exit and error propagation run the applicable destructors.

The core syntax works in C++20. Select `--std c++23` for the standard error-domain headers.

The example in `examples/cpp/herbceptions` exports a channel-offset calculation. It requires no host imports. With an installed matching C++ site profile, build it from the SDK root with the following command.

```sh
bin/wrcc --std c++20 --reactor --export _start --export offset \
    examples/cpp/herbceptions/channel.cpp -o channel.wasm
```

| Setting | Effect |
| --- | --- |
| `--herbceptions` (default) | Enable typed error returns and link the target's static error-domain runtime on demand. |
| `--no-herbceptions` | Compile conventional C++ with the same Wasm compiler. This also allows existing identifiers that would otherwise be extension keywords. |
| `--eh` / `--no-eh` | Select the sysroot for conventional C++ unwinding. Typed error returns work independently of this choice. |
| `--mte` / `--no-mte` | Select the matching instrumented or uninstrumented sysroot. A production MTE build requires a reviewed release for the selected producer, profile and VM. |

For Xmake use `set_wros_profile({herbceptions = true, eh = false, std = "c++20"})` on a C++ target. Select a site whose signed defaults match this profile, or supply the toolchain and corresponding sysroot manifest explicitly. The same profile applies to each translation unit of a static target. `-c` produces a sealed WROS object and a final `wrcc` invocation links the objects.

For a local producer build use `tools/wasm/memtag/build_producer.py --producer herbceptions --bootstrap NATIVE_LLVM --work WORK`. Pass its `producer-build.json` to `build_sysroots.py --producer herbceptions --producer-receipt RECEIPT` when building each guest closure. The compiler starts from the official LLVM 23.1.5 release (`llvmorg-23.1.5`, commit `392dfff97d29b59d77e5cac6d4b6ef2585fe7117`). WasmMTE and the Herbceptions backport are separate patch series. The language feature originates from fork commit `218014296779772a4edbe63eff3fe6fe0ba92390`. The producer build and sysroot receipts identify their sources and binaries. Site qualification additionally executes the resulting guest on both VM engines. A site provisioned for the previous C++ compiler needs a new toolchain and qualification.

[WasmMTE qualification and signing](memory-qualification.md) · [Xmake controls](xmake.md)
