# Objective-C 与 Objective-C++ 工具链

[English](README.md)

`wroc` 和 `wrocxx` 的原生入口位于 C 系列共用的 LLVM 23.1.5 源码树。Clang 允许 WebAssembly 选择 GNUstep 2.0 ABI，向 nil 接收者发送消息时按声明的返回类型生成零值。版本记录列出了已集成的源文件及其上游 Git 对象。[编译器版本](upstream.json)

源码构建使用与 C、C++ 相同的 WASIp1 libc、libc++、compiler-rt 和 LLD。每套 sysroot 都按选定的指针 ABI、MTE 和线程模型构建 GNUstep libobjc2 v2.3 及 WROS 绑定归档。编译应用时，前端校验相应目标库和头文件。EH 档使用 libc++abi 实现标准 Wasm 异常展开，no-EH 档在编译时拒绝异常语法。运行时禁用可执行的块跳板。各宿主和配置的安装、运行结果见[验收记录](../../../document/qualification/objc-library-matrix.json)。[运行时源码](../../runtimes/objc/upstream.json)
