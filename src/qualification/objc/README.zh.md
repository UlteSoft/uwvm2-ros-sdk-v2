# Objective-C 和 Objective-C++ 开源库验收

[English](README.md)

从 SDK 外部项目使用已安装的 `wroc` 和 `wrocxx`，按 wasm32 或 wasm64、MTE、线程、EH 四个维度生成 16 种 Core Wasm。验收程序使用指定的 u2ros VM，在 INT 和 AOT 中运行同一个客体。以下命令可在验收 namespace 中执行，各路径指向相应的安装目录或已下载的测试源码。

运行前按项目验收记录核对 VM 的源码提交、源码树和宿主二进制 SHA-256。使用独立构建时，传入 `--vm-receipt /path/to/receipt.json`。独立挂载测试目录时，使用 `--vm-target` 指定已审阅的 `runtime-qualification.json`。

```sh
python3 -I -B "$QUALIFICATION/objc/matrix.py" \
  --objc-sdk "$OBJC_SDK" --objcpp-sdk "$OBJCPP_SDK" \
  --vm "$U2ROS" --wrwat "$WRWAT" \
  --work "$PWD/.tmp/objc-library-matrix" --jobs 4
```

`QUALIFICATION` 指向同时含有 `cfamily` 和 `objc` 的源码目录。使用空的输出目录。重复传入 `--case` 或 `--profile` 可复现指定用例，例如 `--case chromium-swizzler --profile wasm64-wasip1-threads-eh-mte`。每格保留命令、编译器与库摘要、实际导入、程序输出和各引擎判定。[用例清单](cases.json) · [固定的上游提交、许可证与文件摘要](upstreams.json)

- GCC 的 `Object.m` 检查实例身份、实际类和继承关系。编译时替换根类名称，以便与 GNUstep 自带的 `Object` 同时链接。
- ObjFW 的 `OFCRC32.m` 以已知数据验证 CRC32。Chromium 的 `ScopedObjCClassSwizzler.mm` 检查方法交换、原 IMP 调用和 C++ 析构后的方法恢复。每个组件先单独编译并归档，再链接客户端。Chromium 的调试断言和编译器标注适配保存在 `ports/chromium`。
- GNUstep libobjc2 的上游用例覆盖 category 分派、引用计数、异常重抛和跨翻译单元展开。混合异常客户端另外检查 C++ 析构、Objective-C 类型匹配和 `@finally`。Objective-CPP 的 Foundation 依赖单独记录。

10 个用例共 160 格，其中 112 格计划运行 INT 和 AOT，32 格检查关闭 EH 后的编译诊断，16 格探测 Foundation 依赖。`results.jsonl` 和 `summary.json` 分别保存逐格结果和统计。实际链接数、双引擎通过数、预期拒绝和缺失依赖分别计数。

## 非 MTE 配置的 Wasmtime 对照

`wasmtime_reference.py` 在 Wasmtime 42.0.1 上重放一个宿主的原始 Objective-C 矩阵。默认计划覆盖 10 个用例、8 个非 MTE 配置。其中 56 个客体各与 INT 和 AOT 对照一次，共 112 项。另有 16 格核对关闭 EH 后的编译拒绝，8 格核对缺少 Foundation 的诊断。

在断网的验收环境中只读挂载原始矩阵目录、安装好的 SDK 与 VM 构建收据。`$QUALIFICATION` 下需同时含有 `objc` 和 `cfamily`。按固定版本的 C API 构建参考宿主，将审阅过的构建摘要传给 `$HOST_SHA256`。参考宿主和指令解码器使用重放机器的架构。原始 VM 与编译工具仅供核验摘要，可以来自其他架构。[C API 发布包摘要与宿主构建命令](../cfamily/wasmtime_reference/README.md)

```sh
mkdir -p "$WORK/scratch"
export TMPDIR="$WORK/scratch"
(cd "$QUALIFICATION/cfamily/decoder" &&
  cargo build --offline --locked --release --target-dir "$WORK/decoder-build")
python3 -I -B "$QUALIFICATION/objc/wasmtime_reference.py" \
  --results "$OBJC_MATRIX" --work "$WORK/objc-wasmtime" \
  --host "$QUALIFICATION_HOST" --host-sha256 "$HOST_SHA256" \
  --decoder "$WORK/decoder-build/release/decode-memtag" \
  --vm "$U2ROS" --vm-receipt "$VM_RECEIPT" --vm-target "$VM_TARGET" \
  --objc-sdk "$OBJC_SDK" --objcpp-sdk "$OBJCPP_SDK" --wrwat "$WRWAT"
```

解码器从 SDK 源码树内的 Rust 依赖离线构建，也可以直接传入已有的本机 `decode-memtag`。每次写入独立的空目录。`--case` 和 `--profile` 可重复传入以选择用例和配置。若原矩阵使用早期 C-family 权限策略，传入 `--matrix-policy` 和当时的 `sysroot_suite.py` 以核验工具摘要。当前审阅的策略重新生成 INT、AOT 的完整命令行，核对共享内存、逐项接口决定与授权。

每格核对 wasm 摘要、原始编译命令、运行库收据及归档，以及 VM 源码提交、源码树和可执行文件。脚本从 wasm 读取实际导入签名和内存宽度，逐指令解码核对所选配置。线程格校验 owner 摘要、导出、最小和最大页数。适配器运行原始字节，客体环境和预打开目录为空，标准输入为 EOF。

`results.jsonl` 和每格的 `result.json` 分别给出 INT、AOT 的退出码与两个输出流的对照。`host.log` 记录是否进入 `_start` 以及客体如何退出，`wasmtime.out` 和 `wasmtime.err` 保留原始字节。只有参考客体成功结束、输出满足用例、退出码与两个流均和原矩阵的两个成功引擎完全一致，才记为 `match`。GNUstep 输出指针值的用例同样逐字节比较。`dependency-unavailable` 和 `eh-disabled-rejected` 只计入编译诊断。缺少收据、参考宿主不支持必要导入或权限、超时、观测值不同都会使本轮返回非零。`summary.json` 列出计划客体数、实际开始数和结束数，以及每个引擎的对照计数。
