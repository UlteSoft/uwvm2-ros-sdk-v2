# WAVM 参考实现的 WebAssembly 直接尾调用与 SIMD 通道访存

在 WAVM 提交 `cd7107792bf69ffe62d245ab9479ec5421f13c75` 上应用前四层补丁后，应用第五层以支持直接 `return_call`，随后应用第六层以修正 x86-64 尾调用传参与 SIMD 通道访存宽度。使用固定版本 LLVM 23 构建 x86-64 Linux 参考程序，运行时添加 `--enable return-call`。wasm32 和 wasm64 客体使用相同的宿主 ABI。[构建说明](UPSTREAM.zh-CN.md) · [第五层补丁](core-return-call.patch) · [第六层补丁](tailcc-simd-lanes.patch) · [English](RETURN-CALL.md)

第五层补丁的 SHA-256 为 `8f9d1beb5ff1b5c9e4b50d151aaf0cd4bd44158760391fd6cb35c0e7fa9aaf13`。应用五层补丁后，`Lib/LLVMJIT/EmitCore.cpp` 的 SHA-256 为 `92ccff37730dbbdd3170e9ccbd15a3295d316d6a5a300b26a662071b50c394f0`，`Lib/IR/Validate.cpp` 的 SHA-256 为 `28a3c707bb28d67941029256498804a15d5da4dcc15e799b54f39dcf8fd41065`。

```sh
git -C WAVM apply "$WAVM_REFERENCE_DIR/core-return-call.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/tailcc-simd-lanes.patch"
(cd WAVM && sha256sum -c "$WAVM_REFERENCE_DIR/PATCHED-SOURCES.sha256")
```

第六层补丁的 SHA-256 为 `2e30dee8b7d8a5344ba503bc5cc1393901cae4285e340165b25af4c4eb4b475e`。校验清单覆盖应用全部六层补丁后的 26 个源码文件，清单本身的 SHA-256 为 `d8ebe9c29b44165b65b921a20629efc3741c9baae08858c48ae9d9bc4e8003c2`。[源码校验清单](PATCHED-SOURCES.sha256)

重新构建后，用相同的迭代次数在两种配置下运行原始 cJSON 文件。

```sh
wavm-build/bin/wavm run --nocache --enable return-call --enable wros-ownership --enable memtag-soft-debug "$GUEST" 100
wavm-build/bin/wavm run --nocache --enable return-call --enable wros-ownership "$GUEST" 100
```

静态解码显示，每个冻结的 cJSON 模块各有三条直接 `return_call` 指令，每个采用默认配置的公共 C 模块各有一条。在这四个文件中，前四层参考实现所缺的操作只有 `0x12`。二进制读取器如果遇到 `return_call_indirect` 或 `return_call_ref`，会在加载时报告相应指令的名称。

验证器解析函数索引，从操作数栈取出被调用方的实参，将其结果类型序列与当前函数的返回类型序列进行匹配，并将后续指令标记为不可达。模块内定义的函数与采用 Wasm 调用约定的导入函数使用相同的代码生成路径。WAVM 通过具有 Wasm 函数入口的包装函数调用宿主导入。被调用方的异常和陷阱会越过已退出的调用帧。[Core 验证规则](https://webassembly.github.io/spec/core/valid/instructions.html) · [Core 执行规则](https://webassembly.github.io/spec/core/exec/instructions.html)

## 尾调用的代码生成

一个有效的调用链依次经过接受 1、14、1 个显式参数的函数，返回六个不同类型的值。第五层构建为第一次跳转生成的机器码遗漏了五个栈参数。固定版本的 LLVM x86 后端将此调用约定下的 `musttail` 当作兄弟调用处理，假定所有栈参数已经位于被调用方对应的栈槽中。[固定版本的 x86 调用实现](https://github.com/llvm/llvm-project/blob/4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89/llvm/lib/Target/X86/X86ISelLoweringCall.cpp)

第六层在 WAVM 的标量优化阶段保留 `musttail`，使调用与返回指令保持相邻。生成机器码或导出 LLVM IR 前，JIT 检查返回指令确实原样转交整个调用结果，然后选用 `tail call tailcc`。在 x86-64 平台，双方使用固定参数的 `tailcc`、采用静态重定位且满足上述返回形式时，LLVM 保证生成尾调用。调用点严格使用被调用方的函数原型，调用方自身可以具有不同的参数列表。后端将实参放入相应的寄存器和栈槽，并在双方参数区大小不同时移动返回地址。[LLVM 调用契约](https://github.com/llvm/llvm-project/blob/4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89/llvm/docs/LangRef.rst) · [x86 平台条件](https://github.com/llvm/llvm-project/blob/4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89/llvm/docs/CodeGenerator.rst)

ABI 返回值包含上下文指针和直接返回的结果。Wasm 结果达到三个时，被调用方将整组结果写入该上下文。各模块即使启用不同的特性，其 Wasm 函数、调用点和宿主入口包装函数也采用一致的调用约定。宿主须为使用 64 位指针的 Linux ELF x86-64 平台。尾调用双方各支持最多 4,094 个显式参数，为 x86 返回指令的 16 位退栈立即数留出对齐空间。更大签名的普通调用沿用原有快速调用约定。JIT 缓存版本 7 和原生实例符号 `biasedInstanceId.tailcc.v2` 用于识别修正后的目标文件。

## SIMD 通道访存宽度

在 SHA-256 为 `3c021383817f0895ad8cd09ebdb3d81c11d1ab42aad0959cfe66f4699579968e` 的带标签 wasm32 LZ4 模块中，第五层构建在 `__original_main+1567` 处触发标签异常。文件偏移 `0x15fa` 处的指令为 `v128.store64_lane`，通道索引和地址偏移均为 0。原实现先后在包装函数和辅助函数中对自然对齐的指数值执行移位，将一次 8 字节写入交给 `wros.checkSpan` 按 256 字节检查。第六层对全部八种通道读写形式只做一次换算。边界和软件标签检查覆盖实际访问的 1、2、4 或 8 字节，跨越两个标签粒度单元时会检查两侧。[SIMD 通道修正补丁](tailcc-simd-lanes.patch)
