# 官方宿主工具

SDK 安装器从 xmake-io 获取 Xmake，从 UlteSoft 获取 uwvm2-ros。两个命令安装到所选 SDK 的 `bin/`。安装清单 `share/host-tools/origins.json` 记录上游提交与可执行文件 SHA-256。同一前缀的缓存可复用已校验的下载和已构建的工具。[Xmake 官方发行版](https://github.com/xmake-io/xmake/releases/tag/v3.0.5) · [VM 官方仓库](https://github.com/UlteSoft/uwvm2-ros)

x86-64 使用 Xmake 3.0.5 官方 Linux 二进制。i686、AArch64、ARM 软浮点和硬浮点宿主从官方发行源码构建原生 Xmake，需要 C/C++ 编译器和 GNU Make。

VM 源码安装按 `src/host-tools/uwvm2-ros/UPSTREAM.json` 固定的 Git 提交和树获取源码。Xmake 构建解释器与 LLVM AOT 引擎。宿主需要兼容 LLVM 23 的 C++26 工具链、LLD、Python、CMake、Ninja、GNU Make、Perl 及该提交需要的 Linux 开发文件。首次构建需要为 LLVM 和运行时构建目录预留项目磁盘。安装完成后，项目可以使用该前缀离线构建与运行。

当前验收记录列明实际运行的源码树、宿主二进制以及待验项目。[运行验收](../qualification/runtime-qualification.json) · [English](../en/host-tools.md)
