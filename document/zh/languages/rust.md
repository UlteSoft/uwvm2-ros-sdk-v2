# Rust

ABB Rust 默认安装原生 Rust 1.98.0 的 `wrrs`、配套编译器动态库和 SDK 的 Wasm Clang、LLD。Linux x86-64 宿主需提供含 `GLIBC_2.39` 的 glibc、含 `GLIBCXX_3.4.32` 的 libstdc++，以及 libgcc 和 zlib。将 `revision` 设为登记了两个 Rust 发行包的公开 SDK 完整提交号，在自己的工程目录执行安装。

```sh
python3 -I -B install.py install --commit "$revision" --platform abb --language rust --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
```

`wrrs` 使用内置目标定义，以及 SDK 附带的 `core`、基础宏和编译器内建函数源码，编译 SDK 以外的 `no_std` crate。每次构建在输出文件旁生成来宾 sysroot。两种指针宽度都使用包内链接器，无需安装 Rustup。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrrs" main.rs -o guest.wasm
"$UWVM_ROS_SDK_ROOT/bin/wrrs" --edition 2024 --library sensors ./sensors/lib.rs main.rs -o guest.wasm
"$UWVM_ROS_SDK_ROOT/bin/wrrs" --target wasm64 --memory64 main.rs -o guest64.wasm
```

使用当前 SDK 从源码构建时，指定独立命令 `rebuild`、选定的平台和语言，以及 `--jobs 8`。这会获取可编辑的编译器、LLVM 源码，以及官方 Rust 1.97.1 的三个 x86-64 Linux stage0 归档。安装器校验 Git/LFS 输入，重建程序再依据 Rust 的 `src/stage0` 锁文件逐一校验归档，将引导工具链安装到工作目录。Cargo 使用随库依赖离线构建。宿主需准备 Python 3.12+、原生 C/C++ 编译器和系统开发头文件、CMake、Ninja、Git 及 GNU binutils。如显式指定 `--rust-bin /path/to/1.97.1/bin`，安装器使用该目录中的匹配工具链，并跳过三个归档的下载。

来宾须提供 `#[panic_handler]` 并导出 `_start`。默认使用 Rust 2021。通用 crate 可用 `uwrosv2` 或 `u2rosv2` 引用。ABB 安装中的 `abb` 和 `wros_observation` 指向同一 crate，其中 `ros1` 模块提供 RAPID 消息和服务类型。可将 `examples/abb/rust/ros1` 整目录复制到 SDK 外并用 Xmake 构建。[Xmake 指南](../install-xmake.md)

默认配置为 wasm32、Wasm Core 3、标准 Wasm EH、WasmMTE 和单线程。`--no-eh` 使用 panic-abort。开启 EH 时，rustc 可生成异常展开时的清理代码，panic 的具体行为由来宾的 handler 决定，示例在 panic 时触发 trap。当前来宾提供 Rust core 和编译器内建函数，不含 std 的 panic 捕获或堆分配器。`--no-mte` 可独立关闭 WasmMTE。`--memory64` 控制虚拟机能力，`--target` 控制指针 ABI。wasm32 的 `--threads` 构建导入有上限的共享内存，部署方须提供内存所有者。当前配置未实现 Rust 线程启动 API 或 wasm64 线程 ABI。

使用上游绑定模式时，选择 `--mode bindings --no-mte`，并在离线前为上游工具链安装 `wasm32-unknown-unknown` 目标。此 Xmake 模式用 `WROS_RUSTC` 或 PATH 中的 rustc，采用 wasm32 单线程和 panic-abort。[Rust 官方目标文档](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html)

冻结源码在断网环境重建的两个 ELF 及其 tar.xz 归档均与发行包逐字节一致。公开候选 ba811556 从 GitHub 默认安装了原生 Rust 编译器，生成的 ABB wasm32、wasm64 工程均通过 INT/AOT。该候选使用外部 Xmake 与 VM。[源码和二进制对比、实际导入表与用例](../../qualification/abb-rust-ba811556.json)
