# Flang for Core Wasm

[简体中文](README.zh.md)

The Fortran frontend, Flang runtime and MLIR come from LLVM 23.1.5. The shared LLVM, Clang and CMake sources are in the SDK's C compiler directory. The release record gives the full upstream commit, the three Git tree IDs, the license files and the embedded SDK changes. [Source record](upstream.json) · [Shared compiler sources](../cc/llvm-project/)

The merged target and descriptor changes cover the single-value C calling convention, pointer-sized intrinsic kinds, assumed-size indices and C descriptors for wasm32 and wasm64. The guest runtime changes cover checked extents, strides and allocation. The IR pass selects target-width descriptor bounds and attaches WasmMTE attributes before optimization. [Target lowering](llvm-project/flang/lib/Optimizer/CodeGen/Target.cpp) · [Descriptor layout](llvm-project/flang/include/flang/Optimizer/CodeGen/DescriptorModel.h) · [IR pass](mark_mte.cpp)

The native frontend build uses the LLVM source layout with sibling projects named `llvm`, `clang`, `mlir`, `flang` and `flang-rt`. From the SDK checkout, assemble that layout and select the Wasm backend as follows. The clean SDK rebuild, linked runtime, installed `wrf` and guest runs on this exact source revision remain pending.

```sh
mkdir -p .tmp/flang/source .tmp/flang/temp
export TMPDIR="$PWD/.tmp/flang/temp" TMP="$PWD/.tmp/flang/temp" TEMP="$PWD/.tmp/flang/temp"
cp -a src/compilers/cc/llvm-project/. .tmp/flang/source/
cp -a src/compilers/fortran/llvm-project/. .tmp/flang/source/
cmake -S .tmp/flang/source/llvm -B .tmp/flang/build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_DISABLE_PRECOMPILE_HEADERS=ON \
  '-DLLVM_ENABLE_PROJECTS=clang;mlir;flang' -DLLVM_TARGETS_TO_BUILD=WebAssembly \
  -DLLVM_DEFAULT_TARGET_TRIPLE=wasm32-unknown-wasip1 -DLLVM_ENABLE_ASSERTIONS=ON \
  -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_INCLUDE_BENCHMARKS=OFF \
  -DLLVM_INCLUDE_DOCS=OFF -DLLVM_ENABLE_BINDINGS=OFF -DLLVM_APPEND_VC_REV=OFF \
  -DLLVM_ENABLE_ZLIB=OFF -DLLVM_ENABLE_ZSTD=OFF -DLLVM_PARALLEL_LINK_JOBS=1
cmake --build .tmp/flang/build --parallel 4 --target flang llvm-config
```

Ten migrated C and Fortran inputs exercise address widths, C interoperability, descriptor errors and neighboring stack or storage allocations. They require a linked guest and a matching capability provider for their runtime checks. [Regression inputs](../../qualification/fortran/)
