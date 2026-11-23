# D frontend and runtime

[中文](README.zh.md)

LDC v1.41.0 contains the DMD frontend, the LLVM WebAssembly ABI implementation and druntime. Phobos is materialized at the Git submodule commit selected by that release. The source manifest records both full Git commits, included directories and the corresponding licenses. [Source manifest](upstream.json) · [LDC license](upstream/LICENSE) · [Phobos license](upstream/runtime/phobos/LICENSE_1_0.txt)

The prior SDK's BetterC configuration disables automatic linkage of the host standard library. Its guest entry calls `extern(C) uint wros_main()` and traps on a nonzero result. Both source files are available for port review. The WebAssembly ABI implementation determines how D arguments and return values cross function boundaries. [BetterC configuration](betterc/frontend.conf) · [Guest entry](betterc/entry.c) · [Wasm ABI](upstream/gen/abi/wasm.cpp)

The upstream host build needs CMake, Ninja, a compatible LLVM development installation and a bootstrap D compiler as documented by LDC. From the SDK source root the compiler-only target uses the following commands. Public `wrd` selection, the guest druntime and Phobos, and external vendor projects still require independent qualification. [LDC build prerequisites](upstream/README.md)

```sh
mkdir -p .tmp/ldc/work
export TMPDIR="$PWD/.tmp/ldc/work" TMP="$PWD/.tmp/ldc/work" TEMP="$PWD/.tmp/ldc/work"
cmake -S src/compilers/d/upstream -B .tmp/ldc/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DLDC_BUILD_RUNTIME=OFF
cmake --build .tmp/ldc/build --target ldc2
```
