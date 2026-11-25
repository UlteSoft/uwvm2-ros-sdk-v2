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

## 独立链接 C 模块的共享内存 ABI

测试分别调用已安装的 `wrc` 编译两个 C 模块，两个成品都导入同一个有界 `env.memory`。测试把最后一页分配给共享协议，并核验两个链接器声明的初始内存范围都在这一页之前。公共字节、指针槽、两个模块各自的 16 字节对象均占用独立的对齐粒度。C 端点使用叶函数，无需共享链接器的栈对象或静态数据。标准 Wasm 适配模块按 `i32` 或 `i64` 调用 C 函数。[C 端点、适配模块与运行入口](../../src/qualification/cfamily/shared_memory_abi)

- `raw-offset` 中两个模块各自从预先约定的裸偏移构造地址访问零标签公共字节。每一方写入不同数值，再由另一方读回。
- `pointer-call` 与 `pointer-slot` 分别通过函数签名和共享指针槽传递两端产生的指针。接收方执行 C 指针加常数、返回内部指针并交叉读写。适配模块按完整指针宽度比较双向传递的值。
- `zero-fill` 先写满对象及左右相邻字节，再由另一端初始化 16 字节。测试逐字节核对对象和两侧边界。关闭运行时检查后，MTE 成品返回原始地址，`memtag.storez` 仍须清零。
- `zero-pointer` 用零标签指针访问非零色对象，`zero-allocation` 用非零标签指针访问零色公共字节。运行时启用检查时，普通读和普通写均须以 122 退出，并报告与预期相同的指针、粒度和两个标签。关闭检查后须完成读写并核对数据。

从 SDK 源码目录运行，需要已安装并展开相应线程、无 EH sysroot 的 C SDK、VM 可执行文件和 WABT 的 `wat2wasm`。以下命令用既有离线隔离环境验证一组混合编译模块。

```sh
python3 -I -B src/qualification/cfamily/shared_memory_abi/run.py --isolate \
  --cc-sdk /sdk/c --vm /opt/tools/bin/uwvm2-ros --work .tmp/shared-abi-int32 \
  --width 32 --pair mte-plain --engine int
```

去掉最后一行的三个筛选参数即可覆盖四种编译组合、两个地址宽度、INT/AOT 与运行时检查开关，完整矩阵包括 8 个 C 成品和 192 次独立 VM 启动。用 `--policy on|off` 或 `--case` 可选择更小的范围。隔离测试的结果目录为工作目录下的 `results/`，记录编译收据、Wasm 文件、实际启动命令、日志和每个用例的预期与结果。
