# WasmMTE 标量访存一致性测试

测试在生命周期内的对齐缓冲区中读取或写入四个字节。四个已安装的编译器分别按自己的语言编译同一套源码。标签粒度为 16 字节，wasm32 使用 4 位标签，wasm64 使用 8 位。INT 和 LLVM AOT 在同步软件标签检查模式下运行同一份链接产物。[测试程序](../../src/qualification/cfamily/memtag_suite.py) · [用例源码](../../src/qualification/cfamily/memtag_fixtures) · [English](../en/cfamily-memtag-tests.md)

- **单个粒度。** 独立编译的函数接收一个 48 字节的栈对象，核对编译器生成的指针标签和分配标签。读写位置固定为第 16 至 19 字节（从 0 计），仅改变逻辑指针标签。
- **跨两个粒度。** 从 320 字节对齐缓冲区的第 128 字节开始设置两个粒度的分配标签，再从第 142 字节开始读写四个字节。第一个粒度始终匹配指针，仅对第二个粒度设置指定的标签差值。
- **分配器。** 对 48 字节的活动堆分配，验证三个粒度的标签均与非零指针标签相同，并在对象内写入和读回四个字节。另一次运行保存分配时的整数基址和标签，调用 `free` 后查询这三个粒度的影子标签。所有有效载荷读写均发生在对象生命周期内。
- **关闭 MTE。** 两个位置分别执行正常的读和写，标签差值为零。最终模块中的 WasmMTE 指令数必须为零。

## 从 SDK 源码目录运行

五宿主性能指南提供了线性访存内核在软件和硬件标签检查下的计时结果与复测命令。[内核计时与复测](cfamily-mte-performance.md)

传入已安装的语言前缀、与审阅记录的提交和源码树一致的 VM、指令解码器，以及项目盘上的空结果目录。线程档使用测试程序生成的有界共享内存 owner。解码器使用仓库内的 WasmMTE 指令定义。[解码器源码](../../src/qualification/cfamily/decoder)

```sh
(cd src/qualification/cfamily/decoder && cargo build --release --locked --offline)
python3 -I -B src/qualification/cfamily/memtag_suite.py \
  --cc-sdk /sdk/c --cxx-sdk /sdk/cpp --objc-sdk /sdk/objc --objcpp-sdk /sdk/objcpp \
  --vm /opt/tools/bin/uwvm2-ros \
  --decoder src/qualification/cfamily/decoder/target/release/decode-memtag \
  --work /work/memtag --jobs 4
```

单档示例可追加 `--language objc --profile wasm64-wasip1-threads-noeh-mte --engine int`。三个筛选参数均可重复，仅需提供所选语言的 SDK 前缀。可以用 `--vm-receipt` 和 `--vm-target` 指定单独挂载的 VM 构建收据和修订记录。`--compile-timeout` 与 `--run-timeout` 的单位均为秒。

默认使用零差值、逐个标签位的差值及所有位同时翻转的差值。每个宿主计划构建 64 个模块并运行 VM 2,432 次，包括 256 次普通对照、256 次标签匹配、1,792 次刻意设置的标签不匹配、64 次活动分配观测和 64 次释放后影子标签观测。追加 `--exhaustive` 可以在单粒度访问上验证全部 16 或 256 个差值。

## 解读结果

访问前，guest 输出六个小端 64 位整数，依次为用例编号、标签差值、去标签的字节地址、逻辑标签、首字节和末字节所在粒度的分配标签。访问返回后先输出四字节完成值，再核对数据并清理。每次标签不匹配时，去标签的地址须和同一引擎上的匹配对照相同。进程须以 122 退出，内存保护诊断须指向所选引擎、链接后的标量访问函数、内存 0、记录的指针及出错粒度的地址和标签。VM 提供的指令偏移会写入结果。

`inputs.json` 记录输入与所选工作量。`results.jsonl` 的每一行保存编译收据与 guest 摘要、全模块指令计数、访存函数内实际解码的 `i32.load`、`i32.store` 以及每次启动的阶段、命令与结果。通过行内的 `directory` 和 `log_prefix` 可定位原始标准输出与错误输出。`summary.json` 分别统计构建、执行和各阶段通过的观测数。全部所选构建与执行均通过时，测试程序以 0 退出。
