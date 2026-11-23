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
