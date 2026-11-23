# Odin compiler and target runtime

[中文](README.zh.md)

The source tree contains the frontend, LLVM code generator, base runtime and core library from official monthly release `dev-2026-11a`, commit `9a6991685ddf663956d9836602eb421e141fc443`. The upstream project uses the zlib license. The source manifest identifies each locally changed file by its original Git blob and both content hashes. [Official release](https://github.com/odin-lang/Odin/releases/tag/dev-2026-11a) · [Source manifest](upstream.json) · [License](upstream/LICENSE)

The 17 modified files introduce the `freestanding_wasm64` target in target selection, type checking, LLVM lowering and the target runtime. It uses 64-bit pointers and Wasm memory indices. Upstream's separate `wasm64p32` remains available in this source. The WROS LLVM 23.1.5 IR preparation program checks the incoming target and annotates supported storage for the SDK backend. Its accepted IR restricts exception and memory operations. [Target definitions](upstream/src/build_settings.cpp) · [Wasm allocator](upstream/base/runtime/wasm_allocator.odin) · [IR preparation](mark_mte.cpp)

With Clang, Make and LLVM 20.1.8 development files on a Linux x86-64 host, the upstream build entry for the frontend is shown below.

```sh
mkdir -p .tmp/odin-host
cp -a src/compilers/odin/upstream/. .tmp/odin-host/
cd .tmp/odin-host
mkdir -p work
export TMPDIR="$PWD/work" TMP="$PWD/work" TEMP="$PWD/work"
LLVM_CONFIG=llvm-config-20 make release
```

Public SDK installation, language bindings, vendor projects and the Wasm feature combinations still require independent acceptance. The old compiler binary and measurements belong to their original checkout.
