# Odin 编译器和目标运行时

[English](README.md)

审阅树包含官方月度发行 `dev-2026-11a` 的前端、LLVM 代码生成器、基础运行时和 core 标准库，完整提交为 `9a6991685ddf663956d9836602eb421e141fc443`。上游采用 zlib 许可证。源码清单给出每个修改文件的原始 Git blob，以及上游和移植后的内容摘要。[官方发行](https://github.com/odin-lang/Odin/releases/tag/dev-2026-11a) · [源码清单](upstream.json) · [许可证](upstream/LICENSE)

17 个修改文件覆盖目标选择、类型检查、LLVM 降级和目标运行时，增加 `freestanding_wasm64`，其指针和 Wasm 内存索引均为 64 位。源码也保留上游独立的 `wasm64p32`。WROS 的 LLVM 23.1.5 IR 准备工具核对目标，给支持的存储对象加上后端插装标记。该工具接受的 IR 对异常和内存操作有限制。[目标定义](upstream/src/build_settings.cpp) · [Wasm 分配器](upstream/base/runtime/wasm_allocator.odin) · [IR 准备工具](mark_mte.cpp)

Linux x86-64 上准备好 Clang、Make 和 LLVM 20.1.8 开发文件后，从 SDK 根目录调用上游的前端构建入口。

```sh
mkdir -p .tmp/odin-host
cp -a src/compilers/odin/upstream/. .tmp/odin-host/
cd .tmp/odin-host
mkdir -p work
export TMPDIR="$PWD/work" TMP="$PWD/work" TEMP="$PWD/work"
LLVM_CONFIG=llvm-config-20 make release
```

公开 SDK 安装、语言绑定、厂商工程和 Wasm 特性组合均待独立验收。旧工作区的二进制与运行结果只属于对应的旧提交。
