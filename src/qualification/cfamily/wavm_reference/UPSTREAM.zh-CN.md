# WAVM-mt 验证参考实现

参考源码来自 `trcrsired/WAVM` 的 `mt-2` 分支，固定提交为 `cd7107792bf69ffe62d245ab9479ec5421f13c75`。该提交没有发布标签。上游采用 BSD 三条款许可证，随附文件保留了 WAVM 和 WAVM-MEMTAG 的版权声明。[固定版本](https://github.com/trcrsired/WAVM/tree/cd7107792bf69ffe62d245ab9479ec5421f13c75) · [许可证](LICENSE.txt) · [English](UPSTREAM.md)

二进制编码补丁修改 `Lib/WASM/WASMSerialization.cpp`。补丁 SHA-256 为 `ea30bc3d7681946984c9ccd89aa8ecacb3e3ad9353a0885d43c127e062fe7ca6`，应用后该源文件的 SHA-256 为 `68f172ea5efddd0553ddf9c4172d0e5e2bc767e5c9e4f34892cbf62d49c2b31b`。[编码补丁](wros-memtag-wire.patch)

LLVM 接口兼容补丁修改 `Lib/LLVMJIT/LLVMJIT.cpp`，适配子目标特征的指针和引用接口，并在 Darwin AArch64 平台上要求生成 DWARF 展开信息。补丁 SHA-256 为 `c8ac238e1f650ea8b4d9c09bf2625b5ca974ca5593360b6f51fd3433249e2714`，应用后该源文件的 SHA-256 为 `881d27bfbe2729d177506e44fbc5ef5ac1e164aa780d8f6b6a053292588cbfce`。[LLVM 兼容补丁](llvm23-api.patch)

WAT 输出补丁修正 `Lib/WASTPrint/Print.cpp` 生成的根关键字 `module`。补丁 SHA-256 为 `e4a6d3018b44de06e2fe1b840cbdb7705a06f2964a10d6009b23c612e5d88117`，应用后该源文件的 SHA-256 为 `6299721c4c60b699517f145a49cad920f29e3b7141eb13c71cfd6dcec3682538`。[WAT 输出补丁](wat-module-keyword.patch)

## 指令编码与适用范围

补丁将 WROS 的 19 条共有指令映射到上游 mt-2 的实现。操作号范围为 `0x20..0x2f` 和 `0x36..0x38`。编码依次包含前缀 `0xff`、值为 `0x01010000 | operation` 的 ULEB32 字段和一个 ULEB32 内存索引。验证器检查索引，并根据所选线性内存的地址宽度验证操作数和返回值。[指令签名](../../../host-tools/uwvm2-ros/upstream/src/uwvm2/extension/memtag/instruction.h) · [编码定义](../../../host-tools/uwvm2-ros/upstream/src/uwvm2/extension/memtag/encoding.h)

读取器兼容上述指令原有的 mt-2 `0xfc` 编码。汇编以及重新序列化均输出 WROS 编码和最短 ULEB32 表示。WAVM 的交错 SIMD 指令继续使用 `0xff` 下的 `0x00..0x17` 子操作号。

编码补丁拒绝未知版本、未知域、未知操作号和保留的 `memtag.add`。单独使用编码补丁时，解码器也会识别并在加载时拒绝 `memtag.claim`、`memtag.claimz`、`memtag.reserve`、`memtag.activate` 和 `memtag.release`，其中包括位于未调用函数中的指令。这些指令需要按内存跟踪每个分配区间的所有权和生命周期。

## 私有内存分配的所有权

可选的所有权补丁在 WAVM 的 IR、验证器、LLVM JIT 和运行时实现五条 WROS 分配指令。先应用二进制编码和 LLVM 兼容补丁，再应用本补丁。补丁 SHA-256 为 `e49757fef93d47ed43542ad9b8c264712019cc4382bec8888fa2886b8f815609`。新增源文件 `Lib/Runtime/WROSOwnership.cpp` 的 SHA-256 为 `bcdb556a236d6c9c1850629cc7e1b95d9374c7c6d1a9e82deeaf6aeb4bfaf03c`。行为依据为 `UlteSoft/uwvm2-ros` 提交 `eeab6e7da6de83ae0bbf8fc49fb93398386af302`。[所有权补丁](wros-private-ownership.patch) · [分配状态转换](https://github.com/UlteSoft/uwvm2-ros/blob/eeab6e7da6de83ae0bbf8fc49fb93398386af302/src/uwvm2/extension/memtag/allocation_transition.h) · [静态标签选择](https://github.com/UlteSoft/uwvm2-ros/blob/eeab6e7da6de83ae0bbf8fc49fb93398386af302/src/uwvm2/runtime/memtag/static_allocation.h)

含有上述指令的模块需要启用 `wros-ownership`。模块本地定义的每个 wasm32 或 wasm64 私有内存分别维护分配记录。启用检查时，起始地址及非零长度必须按 16 字节对齐，新区间的每个粒度单元必须尚未标记。claim 立即设置分配标签，claimz 还将数据清零。reserve 选择并记录标签，原指针仍可访问该区间。activate 发布预留标签。release 检查区间和标签是否完全匹配，恢复父标签并删除记录。旧式标签写入会检查重叠和邻近的分配区间。选择分配标签时排除间隔在 64 字节以内的邻居标签。版本 2 的静态描述符经整体验证后才发布标签，并成为永久分配，优先使用计数最少的合法标签。

此配置下，软件检查覆盖标量访问、批量访问和宿主缓冲区访问所触及的全部标签粒度单元。关闭检查时，所有权指令返回输入指针，claimz 仍检查字节边界并清零。该参考配置拒绝共享和导入的内存、WASI 线程创建、硬件 MTE、客户提供的预编译目标文件以及宿主页面解除映射。运行范围为 64 位宿主上的单线程客户实例。参考实现使用 WAVM 自身的异常处理和宿主分配机制。WROS 专用分配器配额、可重放的熵源、异步报告和迁移超出本次比较范围。

SDK 的 cJSON 验证程序含有全部五种分配指令编码，每个模块都声明了 15 条版本 2 的静态描述符。wasm32 程序的 SHA-256 为 `7f68b9c7ab1b93d6403786af17c1c48e3be1bc681c71de755d76b326457eefc1`，wasm64 程序的 SHA-256 为 `ab824190f3513714178bc097d35de271a7e2c1cbba9e5df3bf79956999396967`。这些哈希标识输入文件。第五、六层补丁实现了这些原始客户程序使用的直接尾调用，并修正了带标签 LZ4 负载的 SIMD 通道检查。[原生 ABI、访存宽度和源码哈希](RETURN-CALL.zh-CN.md)

## 复现构建

在可写目录中，将 `WAVM_REFERENCE_DIR` 设为 SDK 中本目录的绝对路径，将 `LLVM_ROOT` 设为提供 Clang、LLVM CMake 配置和 libc++ 的安装前缀。Linux x86-64 宿主工具链报告 Clang 和 LLVM `23.0.0git`，Clang 标明的 LLVM 源码提交为 `4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89`。此信息标识用于构建 WAVM 的宿主工具链，客户程序的编译器版本另见 WROS SDK 构建记录。[LLVM 固定版本](https://github.com/llvm/llvm-project/tree/4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89)

```sh
git clone --branch mt-2 https://github.com/trcrsired/WAVM.git WAVM
git -C WAVM checkout --detach cd7107792bf69ffe62d245ab9479ec5421f13c75
git -C WAVM apply "$WAVM_REFERENCE_DIR/wros-memtag-wire.patch" "$WAVM_REFERENCE_DIR/llvm23-api.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/wat-module-keyword.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/wros-private-ownership.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/core-return-call.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/tailcc-simd-lanes.patch"
(cd WAVM && sha256sum -c "$WAVM_REFERENCE_DIR/PATCHED-SOURCES.sha256")
cmake -S WAVM -B wavm-build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_C_COMPILER="$LLVM_ROOT/bin/clang" -DCMAKE_CXX_COMPILER="$LLVM_ROOT/bin/clang++" \
  -DLLVM_DIR="$LLVM_ROOT/lib/cmake/llvm" -DCMAKE_CXX_FLAGS=-stdlib=libc++ \
  -DCMAKE_EXE_LINKER_FLAGS=-stdlib=libc++ -DCMAKE_SHARED_LINKER_FLAGS=-stdlib=libc++ \
  '-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O3 -g -DNDEBUG' '-DCMAKE_C_FLAGS_RELWITHDEBINFO=-O3 -g -DNDEBUG' \
  -DLINKER_HAS_WL___GDB_INDEX:INTERNAL=0 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DWAVM_ENABLE_FUZZ_TARGETS=OFF
cmake --build wavm-build --target wavm --parallel 6
sha256sum wavm-build/bin/wavm wavm-build/libWAVM.so.0.0.0
```

仅验证二进制编码时应用前三层补丁，并使用上文各层的哈希进行校验。构建完整参考程序后，将 `GUEST` 设为原始 wasm32 或 wasm64 cJSON 模块路径。两个命令使用相同的迭代次数。

```sh
wavm-build/bin/wavm run --nocache --enable return-call --enable wros-ownership --enable memtag-soft-debug "$GUEST" 100
wavm-build/bin/wavm run --nocache --enable return-call --enable wros-ownership "$GUEST" 100
```
