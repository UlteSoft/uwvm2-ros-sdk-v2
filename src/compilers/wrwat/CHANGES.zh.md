# wrwat 源码与修改记录

[English](CHANGES.en.md) · [上游提交、源码包摘要和补丁摘要](UPSTREAM.json)

本目录是可构建的 Cargo 工程。`src/main.rs` 校验汇编结果并写出 Wasm，`src/cli.rs` 处理命令行编译配置，`src/policy.rs` 按 SDK 目录校验导入接口。SDK 在 `d72ffb5` 引入线性内存标签指令，在 `ad5cf14` 引入原生命令。在 SDK 仓库根目录运行 `git log --follow -- src/compilers/wrwat/src/main.rs` 可以查看后续修改。[标签指令提交](https://github.com/UlteSoft/uwvm2-ros-sdk-v2/commit/d72ffb5d181dce67b5caa72d0633967899fc80ea) · [原生命令提交](https://github.com/UlteSoft/uwvm2-ros-sdk-v2/commit/ad5cf148ee70a79afa4f09333227588832678a37)

## 本地修改

1. `changes/01-reader-feature.patch` 还原 wasm-fuzzer 所用的 WasmMTE 读取器，涵盖独立的特性开关、二进制指令解码、算子定义和操作数校验。[读取器的上游提交](https://github.com/UlteSoft/wasm-fuzzer/tree/5beb8556ee40e249cd5f26449784a79f4616ee5c/vendor/wasmparser-memtag)
2. `changes/02-sdk-text-encoding.patch` 为 wast 添加 WAT 助记符和具名内存解析，为 wasm-encoder 添加二进制编码，并让读取器校验托管内存生命周期指令。

构建树已合入以上修改。若需独立复核，按 `UPSTREAM.json` 下载三个原始 crate，核对各自的 SHA-256，将它们解压到空目录下对应的 `vendor/` 子目录，再按顺序运行两次 `git apply`。生成的 `vendor/` 树应与此工程逐文件相同。比对基线使用上游发布的 crate，保留 Cargo 发布时生成的清单。[上游正式发行版](https://github.com/bytecodealliance/wasm-tools/releases/tag/v1.263.0)

其他 Rust 依赖由 `Cargo.lock` 固定。`registry/` 包含离线构建所用的源码、原始许可文件和 Cargo 校验信息。

## 重建 Linux 宿主工具

从已拉取 Git LFS 对象的 SDK 仓库根目录执行以下命令。通过安装器选择 WAT 源码模式时，它会选取当前宿主所需的输入。构建需要 Python 3.11+、原生 `cc`、binutils、glibc 开发文件、libgcc 和 zlib。脚本从宿主清单指定的官方地址下载并校验 Rust 1.98.0 发行包及所需成员的 SHA-256，再用仓库自带的 Cargo 依赖离线编译。四个 musl 目标通过 Rust 自带的 LLD 22.1.8 和目标标准库提供的启动文件、musl 静态库完成链接。

```sh
python3 -I -B src/compilers/wrwat/rebuild.py --output .tmp/wrwat-native
python3 -I -B src/compilers/wrwat/rebuild.py --host linux-armhf --output .tmp/wrwat-armhf
python3 -I -B src/compilers/wrwat/package_release.py --host linux-armhf \
  --executable .tmp/wrwat-armhf --output-root .tmp/wrwat-release
```

第一条命令按正在运行的 Python 解释器的 ELF ABI 生成工具。第二条命令在 x86-64 上可选择以下五种 SDK 宿主。各宿主的原生源码安装默认使用对应的 GNU Rust 发行包。`--rust-bin /path/to/rust/bin` 可指定已经安装的同版官方工具链及其宿主标准库，musl 构建仍会选取对应的目标标准库归档。`--jobs N` 指定 Cargo 的并行度，`--work DIR` 指定可写的构建临时目录。每次构建应指定一个新的输出文件。

- `linux-x86_64` 使用 `x86_64-unknown-linux-gnu`，通过宿主的 glibc 链接驱动和 GNU strip 构建。原有工具链记录在 `bootstrap.json`。
- `linux-i686` 使用 `i686-unknown-linux-gnu` 生成 `i686-unknown-linux-musl`。两者均需支持 SSE2 的 Pentium 4 级别 CPU。
- `linux-aarch64` 使用 `aarch64-unknown-linux-gnu` 生成 `aarch64-unknown-linux-musl`。在兼容的用户空间，也可用 `--rust-bin` 指定同版官方 AArch64 musl 宿主工具链。
- `linux-arm` 的 `arm-unknown-linux-gnueabi` 编译器需要 ARMv6 或更新的软浮点 GNU 用户空间，静态产物支持 `armv5te-unknown-linux-musleabi`。部署到 ARMv5TE 设备时，可在 x86-64 或 ARMv6+ 机器上编译。
- `linux-armhf` 使用 `armv7-unknown-linux-gnueabihf` 生成 `armv7-unknown-linux-musleabihf`，静态产物使用 ARMv7-A 硬浮点 ABI 和 VFPv3-D16。

Rust 1.98.0 为上述四个 musl 目标都提供标准库，其中只有 AArch64 musl 另有官方原生 rustc 和 Cargo。其余三种 ABI 可按上述 CPU 条件使用 SDK 中相应的官方 GNU 工具链原生构建。每个 `bootstrap/linux-*.json` 列出本机 rustc、Cargo、本机标准库和目标标准库的官方地址及 SHA-256。维护者将四个官方归档放在记录的路径后，可用 `lock_bootstrap.py <带日期的发行清单> --host <SDK 宿主>` 重新生成清单。[Rust 1.98.0 官方发行清单](https://static.rust-lang.org/dist/2026-08-20/channel-rust-1.98.0.toml) · [Rust 1.98.0 目标定义](https://github.com/rust-lang/rust/tree/88d9e12ae178fab0fb5cc050a94da85685d449ea/compiler/rustc_target/src/spec/targets)

打包命令校验 ELF ABI、可执行段入口、编译器和链接器标识，并校验 musl 的静态链接及 ARM 的处理器和浮点属性。命令在输出目录生成程序归档、发行记录和 WAT 语言清单，保留已有宿主清单中的其他语言。省略 `--output-root` 即更新仓库本身。安装器将所选宿主的 `src/compilers/wrwat/release/<host>.json` 安装为 `third-parties/wat-mte/release.json`。
