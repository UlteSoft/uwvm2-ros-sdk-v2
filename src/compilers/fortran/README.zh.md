# 用于 Core Wasm 的 Flang

[English](README.md)

Fortran 前端、Flang 运行时和 MLIR 取自 LLVM 23.1.5，LLVM、Clang 和 CMake 的共享源码位于 C 编译器目录。来源记录列出上游完整提交、三个 Git 子树、许可证、已合入的补丁及旧工作区文件摘要。[来源记录](upstream.json) · [共享编译器源码](../cc/llvm-project/)

已合入的前端改动覆盖 Wasm 的单返回值 C 调用约定、指针宽度对应的 intrinsic kind、假定大小数组下标和 32 位与 64 位 C 描述符。来宾运行时改动检查数组维度、跨距及分配。LLVM IR 处理程序按目标宽度选择描述符边界，并在优化前加入 WasmMTE 属性。[目标 ABI](llvm-project/flang/lib/Optimizer/CodeGen/Target.cpp) · [描述符布局](llvm-project/flang/include/flang/Optimizer/CodeGen/DescriptorModel.h) · [IR 处理程序](mark_mte.cpp)

构建原生前端时，LLVM、Clang、MLIR、Flang 和 Flang-RT 须作为同一源码根下的相邻项目。英文版给出了在项目盘 `.tmp` 拼合源码并使用 CMake 和 Ninja 构建 WebAssembly 后端的命令。本提交仍待净室重建，`wrf` 的 GitHub 安装、来宾运行时链接及 VM 运行也待验收。[构建命令](README.md)

已迁入十个 Fortran 和 C 回归输入，用于检查地址宽度、互操作、描述符错误和栈上或静态存储的近邻分配。执行这些用例还需要完成来宾链接，并为其配置相应能力。[回归输入](../../qualification/fortran/)
