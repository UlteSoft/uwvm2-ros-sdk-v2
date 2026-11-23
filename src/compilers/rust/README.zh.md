# WROS 原生 Rust 编译器

Linux x86-64 的 `bin/wrrs` 从 SDK 的 `lib` 目录加载 Rust 1.98.0 的编译器驱动。它解析来宾工程的 crate 根，在独立进程中用同一 ELF 编译每个 crate。安装器还提供 `bin/rustc` 这个调用名，供 `--print target-list` 等原生查询使用。驱动内置 `wasm32-wasip1`、`wasm32-wasip1-threads` 及 SDK 的 `wasm64-wasip1` 目标定义。每次来宾构建在输出目录旁建立临时 sysroot，从随库源码编译 `core` 及其宏、`compiler_builtins`、SDK 运行时和所选绑定。最终链接使用 `share/toolchains/portable/bin/wasm-ld`。同一 ELF 也安装在 `lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld`，供原生 rustc 会话按 Wasm flavor 查找和调用。[中文 Rust 指南](../../../document/zh/languages/rust.md)

## 源码输入

`upstream` 展开自 Rust 1.98.0 官方源码发行包，对应 Git 提交 `88d9e12ae178fab0fb5cc050a94da85685d449ea`。其中包含 Rust 编译器和标准库源码、bootstrap、根 Cargo 工作区所需的 crate、构建本机和 Wasm 目标所需的 Rust LLVM 22 源码，以及根工作区、bootstrap、library 三份 Cargo.lock 引用的 619 个外部包。官方归档的来源、大小、SHA-256、标签和 stage0 版本记录在 `UPSTREAM.json`。MIT、Apache 2.0 和第三方声明位于 `upstream/LICENSE*`、`COPYRIGHT` 与 `license-metadata.json`，各依赖也保留许可文件。

即使只构建 `compiler/rustc`，bootstrap 也会读取官方 `.gitmodules` 并解析已注册的工具路径。源码树收录了 `rustbook`、`error_index_generator` 和 `rust-analyzer` 的 Rust 工作区，以及 rustbook 通过相对路径引用的 book、reference 工具源码。Cargo vendor 覆盖编译器生产构建。筛选时排除了 Rust Analyzer 编辑器扩展、独立文档站、无关开发工具、编译器及 LLVM 独立测试套件、其他系统的导入库、二进制测试样本、压缩示例数据及 schannel/git2 测试私钥。编译器的 Cargo 锁文件保留上游包摘要，目录内 `.cargo-checksum.json` 描述收录的文件。Rust Analyzer LSP 服务库的许可证链接及 LLVM mlgo 的源码链接均展开为普通文件，供安装器按 Git 对象获取。

## 编译与生成流程

- `upstream/compiler/rustc/src/main.rs` 和 `wros.rs` 选择 SDK 原生入口，用真正的 rustc 会话依次构建 `core`、`compiler_builtins`、SDK 运行时、`u2rosv2`、所选平台 crate、显式依赖与应用。链接根为 `_start`。
- `upstream/compiler/rustc_llvm/llvm-wrapper/PassWrapper.cpp` 在 LLVM 优化前调用 `WrosIR.h`。标记器保留可寻址 Rust 静态对象的信息，为函数与内存对象设置 MTE 属性，拒绝带指令的内联汇编。无需调试输出时，静态对象分类完成后才清除调试信息。
- `upstream/compiler/rustc_target/src/spec` 注册 UWVM 的 wasm64 WASI Preview 1 扩展目标，前端使用相应的指针宽度和调用约定。`runtime.rs` 提供与上游相同的 Wasm EH 语言项和独立于指针宽度的 trap。
- `lower.py` 调用 SDK 提供的 LLVM 23 Clang/LLD，将 Rust bitcode 生成真实的 WasmMTE、标准 EH 或原子操作，然后用 SDK 的 ABI 合约检查最终的导入和签名。

默认使用 wasm32、Core 3、标准 Wasm EH、MTE 和单线程。EH 开启时使用 `panic=unwind` 并支持 unwind 调用的清理路径。应用自行定义 panic handler，示例的 handler 触发 trap。当前提供 Rust core 与编译器内建函数，未提供 std/alloc、带堆分配的 panic 运行时、std 的 catch_unwind、Cargo 自动解析依赖、过程宏或 Rust 线程启动。wasm32 的线程配置导入最大页数有界的共享内存，需由部署方提供所有者。64 位 Preview 1 适配仅支持单线程。MVP 需关闭 EH、memory64 与线程。库中与 C++ 异常运行时和 WASI 匹配的归档目前限 Core 3、EH/MTE 开、单线程这一组合。

## 重建入口

准备 Linux x86-64、Python 3.12 或更高版本、原生 C/C++ 编译器和开发头文件、CMake、Ninja、Git、GNU binutils。源码安装会从 Rust 官方固定日期的发行地址获取官方 1.97.1 的宿主 `rustc`、`rust-std` 和 `cargo`。安装器依据固定的 SHA-256 校验下载，重建程序再依据 `upstream/src/stage0` 核对每个归档后解包，在工作目录中安装三个组件。显式指定 `--rust-bin /path/to/stage0/bin` 可使用已有的同版本宿主 rustc、标准库和 Cargo 并跳过归档下载。LLVM 22 与 stage1 rustc 都从随库源码构建，Cargo 使用随库依赖离线运行。

```sh
work="$PWD/.tmp/rust-release"
python3 -I -B src/compilers/rust/rebuild.py \
    --work "$work/build" --prefix "$work/runtime" --packages "$work/packages" --jobs 8
```

构建结束后，可在登记发行包前为核验准备 ABB 的安装布局，再从 SDK 外编译样例。

```sh
python3 -I -B src/compilers/rust/stage_sdk.py --sdk "$work/runtime" --platform abb
export UWVM_ROS_SDK_ROOT="$work/runtime"
cp -a src/examples/abb/rust/ros1 "$work/abb-ros1"
"$UWVM_ROS_SDK_ROOT/bin/wrrs" --platform abb "$work/abb-ros1/main.rs" -o "$work/abb-ros1/guest.wasm"
```

## 交付包状态

生成阶段在 `--packages` 目录写入各 ELF 的独立 tar.xz，以及记录 SHA-256、安装位置和宿主动态库依赖的 `rust-packages.json`。维护者可以在本地登记生成的候选归档。

```sh
python3 -I -B src/compilers/rust/register_release.py --from "$work/packages"
```

宿主清单已登记上一轮 ABB 诊断重建的 `wrrs` 和 `librustc_driver-aff9448c053be314.so`。两份归档的 SHA-256 分别为 `ed3689868ebfd06651c6497c081d90db1d3e876c8653fa96fb74dfd8bbd4db2a` 和 `8a99747417c5699f26f0c3689e9d16827133dab1145e03642eae58e08527838f`。安装器核验两份归档及其 ELF，将驱动放在可执行体的相对动态库搜索路径中。驱动要求宿主 glibc 提供 `GLIBC_2.39`，libstdc++ 提供 `GLIBCXX_3.4.32`。GitHub 冷安装和独立的断网冻结源码构建已完成，重建的两个 ELF 及两份压缩包均与登记内容逐字节相同。ABB 实际 guest 覆盖两种指针位宽、MTE 和原生异常处理。自带宿主工具的候选还用安装所得 Xmake 和 VM 验证了 C、C++ 与 Rust。[重建对比](../../../document/qualification/abb-rust-ba811556.json) · [自带宿主的运行记录](../../../document/qualification/abb-1259ec52.json)
