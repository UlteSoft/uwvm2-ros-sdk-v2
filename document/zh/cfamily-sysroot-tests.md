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
