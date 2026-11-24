# C 系列执行性能矩阵

每个宿主使用安装所得的 C、C++、Objective-C、Objective-C++ 编译器分别构建开源库。每种语言组合 guest ABI、EH、线程、SIMD 和 MTE 五个开关，共 32 格。五个 Linux 宿主合计 640 格。运行器在每格先核对 INT、LLVM AOT 和可用参考引擎的计算结果，再计时。[验收规范](../../../../document/zh/qualification.md) · [English](README.md)

## 运行

在隔离验收环境中使用 Python 3.11 或更新版本。下列命令从 SDK 源码根目录运行。`C_SDK` 等变量指向分别安装四种语言所得的前缀。`VM` 是本机的 WROS VM，`DECODER` 用于读取实际 Wasm 指令。`CAPI_HOST`、`WASMTIME` 和 `WAVM` 分别指向 Wasmtime C API 驱动、官方 Wasmtime 42.0.1 命令和适配 WROS 指令的 WAVM-mt。单独选择一种语言时，只需提供该语言的前缀。

```sh
suite="$PWD/src/qualification/cfamily/execution_performance"
scratch="$PWD/.tmp/cfamily-execution"
mkdir -p "$scratch/tmp"
export TMPDIR="$scratch/tmp"
python3 -I -B "$suite/matrix.py" --list > "$scratch/plan.jsonl"
python3 -I -B "$suite/matrix.py" \
  --cc-sdk "$C_SDK" --cxx-sdk "$CXX_SDK" \
  --objc-sdk "$OBJC_SDK" --objcpp-sdk "$OBJCPP_SDK" \
  --vm "$VM" --decoder "$DECODER" --wasmtime-host "$CAPI_HOST" \
  --wasmtime-cli "$WASMTIME" --wavm "$WAVM" \
  --work "$scratch/full-host"
```

`--work` 需要空目录。运行器从 VM 的 ELF 识别宿主，用资格记录核对 VM 的提交、源码树和二进制摘要。`--vm-receipt` 与 `--vm-target` 可用于指定已冻结的候选。验收时传入外层启动器生成的 `--isolation-receipt`。ARM 宿主在系统 QEMU 内执行，传入 `--environment system-qemu`。用户态 QEMU 仅记录功能结果。用 `--cpu` 固定逻辑核，默认每格比较采集十对样本。`--language`、`--profile`、`--width`、`--eh`、`--threads`、`--simd` 和 `--mte` 可缩小范围。[解码器源码](../decoder) · [C API 驱动构建说明](README.md#reference-engines)

## 负载与参考引擎

- C 用 LZ4 v1.10.0 压缩、解压十六组 16 KiB 数据，核对还原内容和校验和。计时区间共处理 8 MiB。[负载](lz4.c)
- C++ 用 fast_float v8.0.2 解析 262,144 个字符串，按独立生成的双精度结果校验。[负载](workloads.cpp)
- Objective-C 用 GCC 15.2.0 的两个存活对象执行 65,536 组方法分派。[负载](gcc-object.m)
- Objective-C++ 用 Chromium 143 的作用域方法替换执行 4,096 轮，核对替换、调用原实现和恢复后的结果。[负载](chromium-swizzler.mm)

无 MTE 的产物对照 Wasmtime。C API 驱动支持 SDK 的 wasm64 时钟接口和部分共享内存导入；原生性能比要求实际使用对应宿主的 Cranelift 后端。带 MTE 的产物对照适配的 WAVM-mt，同时用 WROS 运行同一份 Wasm，比较开启和关闭运行时软件检查的耗时。WAVM 私有所有权适配目前只覆盖私有内存。各格单独记录缺少的能力、无法解析的导入和实际运行错误。线程配置的这四个负载都在一个 guest 线程里执行。[WAVM 参考端](../wavm_reference/UPSTREAM.zh-CN.md) · [可选指令专项](../../../../document/zh/cfamily-optional-instructions.md)

## 读结果

每个负载在 guest 内预热，然后用单调时钟测量计算区间。配对执行时轮换引擎顺序。`inputs.json` 记录输入和引擎身份；每格的 `result.json` 记录编译参数、Wasm 摘要、指令统计、导入、正确性及配对结果。`results.jsonl` 汇集各格记录，`summary.json` 汇总已完成数量和各参考端状态。比值的分子是 WROS AOT 用时，分母由该项的引擎名确定。`aot-disabled` 项以同一产物关闭运行时检查的耗时为分母，目标是配对中位数不超过 1.5。退出码 0 表示选中的格均取得所需对照并满足适用阈值，77 表示仍缺对照，1 表示存在失败或超标。
