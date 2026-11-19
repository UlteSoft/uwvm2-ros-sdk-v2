# 使用 wrcc 开发 C++

`wrcc` 基于 LLVM 23.1.5 正式版回移 Herbceptions。核心语法支持 C++20，使用标准错误域头文件时请选 `--std c++23`。

`wrcc` 使用 Herbceptions Clang 的类型化错误返回。函数通过 `return_failure{E}` 声明错误类型，调用方可用 `catch return_failure(表达式)` 取得成功值或错误值。沿错误路径离开作用域时，局部对象执行相应的析构函数。

`examples/cpp/herbceptions` 的示例导出一个通道偏移计算函数，无需宿主导入。安装与配置匹配的 C++ 开发包后，可在 SDK 根目录运行下面的命令。

```sh
bin/wrcc --std c++20 --reactor --export _start --export offset \
    examples/cpp/herbceptions/channel.cpp -o channel.wasm
```

| 选项 | 作用 |
| --- | --- |
| `--herbceptions`（默认） | 启用类型化错误返回，最终链接按符号需要引入目标 Wasm 的静态错误域运行库。 |
| `--no-herbceptions` | 使用同一 Wasm 编译器编译常规 C++。这也允许旧代码继续把扩展关键字用作标识符。 |
| `--eh` / `--no-eh` | 选择传统 C++ 异常展开所用的 sysroot。类型化错误返回可单独开启。 |
| `--mte` / `--no-mte` | 选择带插桩或无插桩的 sysroot。正式 MTE 构建需要与编译器、目标配置、VM 匹配的已审发布记录。 |

Xmake 的 C++ 目标可使用 `set_wros_profile({herbceptions = true, eh = false, std = "c++20"})`。选择默认配置匹配的签名站点，或显式提供工具链和对应的 sysroot 清单。静态库中的各翻译单元使用该目标的配置。单独编译时用 `-c` 生成带校验记录的 WROS 对象，再用 `wrcc` 链接。

本地构建编译器时，运行 `tools/wasm/memtag/build_producer.py --producer herbceptions --bootstrap NATIVE_LLVM --work WORK`。随后在构建各个目标 sysroot 时向 `build_sysroots.py --producer herbceptions --producer-receipt RECEIPT` 传入产出的 `producer-build.json`。生产编译器以 LLVM 官方正式版 `llvmorg-23.1.5`（提交 `392dfff97d29b59d77e5cac6d4b6ef2585fe7117`）为基线，分别叠加 WasmMTE 和 Herbceptions 回移补丁。语言扩展的来源是 fork 提交 `218014296779772a4edbe63eff3fe6fe0ba92390`。编译器与 sysroot 收据记录对应源码和二进制，站点验收还会在 VM 两种引擎中执行产物。旧 C++ 站点切换时需要部署新的工具链并重新验收。

[WasmMTE 验收与签名](memory-qualification.md) · [Xmake 配置](xmake.md)
