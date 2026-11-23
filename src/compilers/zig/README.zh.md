# Zig 0.16.0

[English](README.md)

可编辑的 upstream 目录包含 Zig 0.16.0 全部 21,918 个 Git 文件对象，其中有前端、编译器运行时、标准库、CMake、C 引导程序和上游自带的第一阶段 Wasm 种子。文件内容与执行位均匹配上游 `24fdd5b7a4c1c8b5deb5b56756b9dbc8e08c86a8`。主许可证为 MIT，发行树保留了各第三方声明。[上游标签](https://codeberg.org/ziglang/zig/src/tag/0.16.0) · [来源记录](upstream.json) · [上游构建说明](upstream/README.md)

SDK 的 `mark_mte.cpp` 读取 Zig 输出的 LLVM IR，核对目标数据布局，为 WROS LLVM 后端添加内存标记所需的属性。该文件来自旧 SDK 未提交的工作区，原始摘要见来源记录。构建它需要 LLVM 开发库。上游的 CMake 构建需要 CMake 3.15 以上及 LLVM、Clang、LLD 21.x 开发库。另一条 C 引导路径会生成上游构建说明中列明功能范围的第二阶段编译器。

原生 Zig 编译器的 SDK 安装、断网重建、目标开关、平台接口及独立 VM 运行均待验收。
