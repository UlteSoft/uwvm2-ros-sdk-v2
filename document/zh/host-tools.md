# 官方宿主工具

所选 SDK 提供 `bin/xmake` 和 `bin/uwvm2-ros`。`plan` 和 `install` 都按当前 Python 进程的 ELF ABI 查询发行资产，并在缺件时列出工具和宿主。安装器校验发布的文件，按所选前缀放置工具，并在 `share/host-tools/origins.json` 中记录来源。

x86-64 使用 xmake-io 发布的 Xmake 3.0.5 ELF。i686、AArch64、ARM 软浮点和 ARM 硬浮点使用 Debian 发布的固定版本 Xmake 包。`bin/xmake` 启动脚本按所选 SDK 的相对路径定位 Debian ELF 和资源。未修改的上游二进制从发行方获取，安装缓存按发行资产的 SHA-256 复用下载。[Xmake 官方发行版](https://github.com/xmake-io/xmake/releases/tag/v3.0.5) · [Debian 包清单](../../src/host-tools/xmake/debian-packages.json)

VM 发行清单固定上游提交，在 `tools.uwvm2-ros.hosts` 下按宿主登记资产。单成员 USTAR `.tar.xz` 条目记录实际的 GitHub 发行标签 `tag`、资产文件名 `asset`、格式 `tar.xz`、成员名 `uwvm2-ros`，以及压缩包的 `compressed_bytes`、`compressed_sha256` 和 ELF 的 `bytes`、`sha256`。直接发布的 `elf` 使用 ELF 的长度和摘要。安装时还核对 Linux ELF ABI 及 ARM 浮点调用约定。清单固定了[官方 VM 预发行版](https://github.com/UlteSoft/uwvm2-ros/releases/tag/wros-vm-b27df7428f9f)中的五种 Linux 宿主包。[宿主发行清单](../../src/host-tools/releases.json) · [VM 源码版本](../../src/host-tools/uwvm2-ros/UPSTREAM.json)

独立命令 `rebuild` 从固定的上游发行源码构建 Xmake，按固定 Git 提交和树获取 VM 源码，再构建解释器与 LLVM AOT 引擎。宿主需要兼容 LLVM 23 的 C++26 工具链、LLD、Python、CMake、Ninja、GNU Make、Perl 及该提交需要的 Linux 开发文件。请在前缀下为 LLVM 和运行时构建目录预留磁盘空间。[VM 官方仓库](https://github.com/UlteSoft/uwvm2-ros)

当前验收记录列明实际运行的源码树、宿主二进制以及待验项目。[运行验收](../qualification/runtime-qualification.json) · [English](../en/host-tools.md)
