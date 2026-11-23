# D 前端和运行时

[English](README.md)

LDC v1.41.0 包含 DMD 前端、LLVM 的 WebAssembly ABI 实现及 druntime。Phobos 使用本次发行指定的 Git 子模块提交，已展开为可编辑源码。清单记录两个完整提交、选取的目录和各自的许可证。[源码清单](upstream.json) · [LDC 许可证](upstream/LICENSE) · [Phobos 许可证](upstream/runtime/phobos/LICENSE_1_0.txt)

旧 SDK 的 BetterC 配置关闭宿主标准库的自动链接。客体入口调用 `extern(C) uint wros_main()`，返回非零时产生 Wasm trap。这两个文件均已移入审阅目录。WebAssembly ABI 实现决定 D 函数边界的参数与返回值传递方式。[BetterC 配置](betterc/frontend.conf) · [客体入口](betterc/entry.c) · [Wasm ABI](upstream/gen/abi/wasm.cpp)

构建宿主前端需要 CMake、Ninja、兼容的 LLVM 开发文件和可用于引导的 D 编译器，上游列有版本要求。下面是 SDK 源码根目录中的前端构建命令。公开安装 `wrd`、客体 druntime 和 Phobos，以及外部厂商工程均待独立验收。[LDC 构建依赖](upstream/README.md)

```sh
mkdir -p .tmp/ldc/work
export TMPDIR="$PWD/.tmp/ldc/work" TMP="$PWD/.tmp/ldc/work" TEMP="$PWD/.tmp/ldc/work"
cmake -S src/compilers/d/upstream -B .tmp/ldc/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DLDC_BUILD_RUNTIME=OFF
cmake --build .tmp/ldc/build --target ldc2
```
