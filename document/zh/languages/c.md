# C 工程

使用 `--language c` 安装。复制安装目录中的 `examples/c`，按照[安装指南](../install-xmake.md)设置环境后，在副本中执行 `xmake build` 和 `xmake test -j1`。

`<uwrosv2/scene.h>` 提供 C 场景 API。`uwrosv2_abi()` 调用版本查询导入。使用已配置资源时，先按部署别名打开能力，逐次检查返回状态，完成后关闭资源和能力。各域的头文件定义了相应的句柄与缓冲区接口。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrc" --reactor --export _start --std c17 main.c -o guest.wasm
```

`wrc` 是内嵌编译器的 LLVM 可执行文件，与匹配的链接器、归档器及 Wasm sysroot 一起安装。`--reactor --export _start` 用于链接由 guest 实现的入口。迁移示例 `examples/c/migration/zlib` 展示在 SDK 中使用现有 C 库。

驱动会自动查找随包 C 绑定和所选平台的 C 头文件。WASIp1 C 库头文件可在 `include/sysroot/c/` 中逐份查看，编译时按标准名称引用，例如 `<stdio.h>`。C++ 工程也可引入这套 C 绑定，全部 C 入口在 C++98/03 下声明为 `throw()`，从 C++11 起为 `noexcept`。

## WasmMTE 指针相减

C、C++、Objective-C 和 Objective-C++ 中，同一数组内的指针相减，结果是带符号的元素距离。例如两个指针指向 12 字节的结构体，线性地址相距 60 字节，元素距离就是 5。开启 `--mte` 后，Clang 对线性内存 0 的数据指针先执行 `memtag.sub`，再除以元素大小。`--no-mte` 使用普通指针减法。两个 `uintptr_t` 值相减始终采用完整的无符号整数位宽，包括从指针显式转换得到的值。

开启 MTE 的翻译单元可以显式选择按字节计算的操作。下列签名中的 `ptrdiff_t` 来自 `<stddef.h>`，`uintptr_t` 来自 `<stdint.h>`。

```c
ptrdiff_t __builtin_wasm_memtag_sub(int memory, void *lhs, void *rhs);
uintptr_t __builtin_wasm_memtag_sub_raw(const void *lhs, const void *rhs);
ptrdiff_t __builtin_wasm_memtag_sub_uintptr(int memory, uintptr_t lhs, uintptr_t rhs);
```

- `__builtin_wasm_memtag_sub` 接收两个指针，返回二者线性地址的带符号字节差。SDK 主内存的索引取常量 `0`。
- `__builtin_wasm_memtag_sub_raw` 对包含标签位的完整指针表示做减法，结果以字节为单位，在 wasm32 上按 2³² 取模，在 wasm64 上按 2⁶⁴ 取模。
- `__builtin_wasm_memtag_sub_uintptr` 将两个整数的位模式解释为指针，对指定内存执行 `memtag.sub`，返回带符号的字节差。结果在 wasm32 上为 32 位，在 wasm64 上为 64 位。wasm64 上 `uint32_t` 实参按零扩展转换，`uintptr_t` 实参保留全部 64 位。带符号的 32 位值如果表示无符号偏移，先转换为 `uint32_t` 可明确零扩展。

内存索引必须是整数常量表达式，传入运行时变量会产生编译诊断。选择 `--no-mte` 时，所有 `__builtin_wasm_memtag_*` 的 `__has_builtin` 结果均为 `0`，直接调用会报告未知内建函数或未声明的标识符。在开启 MTE 的翻译单元中，`no_sanitize("memtag")` 和 `disable_sanitizer_instrumentation` 会关闭相应函数内的自动指针减法转换。显式调用内建函数仍按所选操作执行。
