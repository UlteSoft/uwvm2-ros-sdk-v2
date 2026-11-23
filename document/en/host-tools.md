# Official host tools

The SDK installer obtains Xmake from xmake-io and uwvm2-ros from UlteSoft. The selection puts both commands in its own `bin/`. Each installation records the upstream commit and executable SHA-256 in `share/host-tools/origins.json`. The prefix cache reuses verified downloads and previously built tools. [Xmake release](https://github.com/xmake-io/xmake/releases/tag/v3.0.5) · [VM repository](https://github.com/UlteSoft/uwvm2-ros)

On x86-64 the installer verifies the official Xmake 3.0.5 Linux executable. On i686, AArch64, ARM EABI and ARM hard-float it builds native Xmake from the official release source with a C/C++ compiler and GNU Make.

The current VM source installation fetches the commit and tree pinned in `src/host-tools/uwvm2-ros/UPSTREAM.json`. Xmake builds its interpreter and LLVM AOT engine. A native build needs the LLVM 23 compatible C++26 toolchain, LLD, Python, CMake, Ninja, GNU Make, Perl and the Linux development files required by that revision. The first build also needs project disk space for its LLVM and runtime build trees. The installed compiler and Xmake projects can use the resulting selection offline.

Consult the current runtime qualification for the tested source trees, host binaries and outstanding cases. [Runtime qualification](../qualification/runtime-qualification.json) · [中文](../zh/host-tools.md)
