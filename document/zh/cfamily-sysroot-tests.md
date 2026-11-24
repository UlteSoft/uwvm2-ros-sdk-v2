# WASIp1 sysroot 库测试

测试通过已安装的 `wrc` 或 `wrcc` 编译上游程序，再使用 u2ros 的 INT 和 LLVM AOT 运行同一份 Core Wasm。矩阵组合 wasm32、wasm64 和 MTE、线程、异常处理三个独立开关，共 16 档。

[用例清单](../../src/qualification/cfamily/cases.json) 记录了每个源文件。LLVM 用例来自 23.1.5。Open POSIX 用例来自 WASI SDK 34 采用的 wasi-libc。libc-test 使用该版本 wasi-libc 指定的提交。pthread 一致性用例在开启线程的八档运行，其余用例覆盖全部十六档。[LLVM 源码](https://github.com/llvm/llvm-project/tree/392dfff97d29b59d77e5cac6d4b6ef2585fe7117) · [wasi-libc 源码](https://github.com/WebAssembly/wasi-libc/tree/2e6fb9d8ee0cdf9e431fbcabe8af3115de000a13) · [libc-test 源码](https://github.com/bytecodealliance/libc-test/tree/18e28496adee3d84fefdda6efcb9c5b8996a2398)

在验收 namespace 内运行[测试程序](../../src/qualification/cfamily/sysroot_suite.py)。传入已安装的 C、C++ 前缀，对应编译器源码，已安装的 WAT 汇编器、VM、指令解码器和项目盘上的空目录。示例使用隔离环境内的挂载路径。

运行前按项目验收记录核对 VM 的源码提交、源码树和宿主二进制 SHA-256。使用独立构建时，传入 `--vm-receipt /path/to/receipt.json`。独立挂载测试目录时，使用 `--vm-target` 指定已审阅的 `runtime-qualification.json`。

```sh
python3 -I -B /repo/src/qualification/cfamily/sysroot_suite.py \
  --cc-sdk /sdk/c --cxx-sdk /sdk/cpp --compiler-sources /repo/src/compilers/cc \
  --vm /opt/tools/bin/uwvm2-ros --wrwat /sdk/wat/bin/wrwat \
  --decoder /opt/tools/bin/decode-memtag --work /work/results --jobs 8
```

`inputs.json` 记录工具、清单和测试程序的摘要。`results.jsonl` 每行列出源文件、配置、编译参数，以及成功构建的 Wasm 的摘要、指令计数、实际导入和各引擎结果。每个程序的目录保留编译器、解码器、INT 和 AOT 的输出。`summary.json` 分别统计构建与执行。上游主动跳过、POSIX 前置条件未满足、超时和编译失败各有单独状态。有适用程序未通过双引擎时，测试程序以非零退出。

测试第三方库时，增加 `--suite external`，并为结果另选一个空目录。14 个程序各自跑遍 16 档。LZ4 检查压缩与解压往返，cJSON 运行三组上游 Unity 用例，uthash 把四个上游程序的输出与上游答案逐字节比较，fast_float 运行四个数值解析程序。SDK 的两个测试客户端分别验证 pugixml 的 XPath 查询与节点修改，以及 TinyXML-2 的内存序列化与解析。清单固定每个项目的提交，并按 Git blob 核对源码、测试及许可证。[第三方源码与程序清单](../../src/qualification/cfamily/external-libraries.json)

Clang 指针减法另有编译回归，覆盖两种整数位宽、C 与 C++、普通类型化指针差、显式减法内建及关闭 MTE 后的诊断。[Clang CodeGen 与 Sema 回归源码](../../src/qualification/cfamily/clang)

WasmMTE 标量测试覆盖四个前端，检查标签匹配、单粒度与跨双粒度标签不匹配，以及堆分配活动期间和释放后的影子标签。[运行 WasmMTE 一致性测试](cfamily-memtag-tests.md)

## Wasmtime 对照

使用固定版本 Wasmtime 42.0.1 的 C API 适配器，每次读取一个构建宿主的 sysroot 验收结果。对照机使用可在本机执行的适配器和指令解码器，只读挂载同版 SDK 源码和原始结果。保留 `inputs.json`、`results.jsonl`、`summary.json` 及八个无 MTE 配置目录，含编译收据、原始输出与共享内存 owner。[适配器构建说明](../../src/qualification/cfamily/wasmtime_reference/README.md)

```sh
python3 -I -B /repo/src/qualification/cfamily/wasmtime_reference/compare.py \
  --suite sysroot --host /tools/qualification-host --decoder /tools/decode-memtag \
  --compiler-sources /repo/src/compilers/cc --results /original/sysroot \
  --work /work/sysroot-reference --jobs 2 --timeout 180
```

重放生产验收时，可传入 `--qualification-receipt /original/evidence/sysroot-receipt.json` 核验逐项记录和汇总的摘要，使用 `--host-sha256` 传入适配器的可信构建摘要。结合 `--vm`、`--vm-receipt`、`--vm-target` 可以核对原宿主的 VM 二进制、收据及经审阅的提交和源码树，支持跨宿主架构对照。

完整清单含 2,464 个源码与配置组合，其中 1,232 个关闭 MTE。Open POSIX 仅在开启线程的配置下运行。使用 `sysroot_suite.py --case` 或 `--profile` 产生的结果按原始选择单独统计。驱动核对资格计数、源码、guest 与编译收据，重新解码指令，检查实际导入、共享内存上下限及 INT、AOT 的完整命令行。适用的线程档加载原始 `env.memory` owner。

原始命令授予 `args` 权限时，驱动从已核验的 INT 和 AOT 命令中读取 `--run` 后的 guest 绝对路径，作为唯一的参数 `argv[0]`。即使对照机上的挂载路径不同，guest 也会收到原始路径。每行的 `wasip1_policy` 以 `guest-argv0` 记录该值。`args_get` 和 `args_sizes_get` 使用 32 位指针和长度，对应的 `_wasm64` 接口使用 64 位指针和长度。

单独验证参数 ABI 时，从已核验 SHA-256 的 Wasmtime 42.0.1 C API 发行包中取出 `libwasmtime.so`，挂载到 `/tools/libwasmtime.so`。脚本调用 `wasmtime_wat2wasm` 汇编测试模块，在每种指针宽度下检查授权时写入的参数字节，再分别核对未授予 `args` 和拒绝接口时的错误码。新输出目录中的六份宿主日志均应以 `end returned 0` 结尾。

```sh
python3 -I -B /repo/src/qualification/cfamily/wasmtime_reference/check_args.py \
  --wasmtime-lib /tools/libwasmtime.so --host /tools/qualification-host --work /work/args-check
```

`results.jsonl` 每行给出源码、配置和原始资格结果。只有 Wasmtime 的 guest 正常退出且退出码为零，原 INT 和 AOT 均通过，并且三者的退出码、stdout 和 stderr 均一致，才记为 `match`。运行目录保留原始字节输出和 `host.log`。汇总报告记录实际 guest 启动与终止次数、各档和各库的状态，以及参考宿主缺少的每项导入或授权。

上游明确输出跳过、链接缺少 `sem_unlink`、固定版本的上游 `lsearch` 使用过短输入记录，各有单独状态。SDK 的全宽记录移植用例独立记账。对于导入 `wasi.thread-spawn`、`clock_res_get`、`fd_pread` 或获准通过 `poll_oneoff` 执行实时时钟等待的用例，记录参考宿主缺少的导入和授权。这些项的双引擎对照状态为 `unavailable`。退出码 0 表示选中的无 MTE 项全部匹配。77 表示适用项全部匹配，其余项存在明确限制。1 表示存在观测差异、意外失败或验收证据错误。
