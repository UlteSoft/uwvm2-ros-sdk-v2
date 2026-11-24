# C、C++、Objective-C 和 Objective-C++ 的 VM 源码调试、完整快照还原及签名热更新

默认矩阵在十六档 guest 配置上验证四个已安装前端的三项 LLVM AOT 能力，每宿主计划 192 项。Linux x86-64、i686、AArch64、ARM 软浮点及 ARM 硬浮点共计划 960 项。入口从受测 VM 的 ELF 头识别宿主 ABI，同时记录控制器 CPU 架构及可选的模拟器命令。[资格入口](../../src/qualification/cfamily/debug_suite.py) · [源码用例](../../src/qualification/cfamily/debug_fixtures) · [English](../en/cfamily-debug-tests.md)

## 重现一个宿主的测试

使用内存上限 64 GiB、零交换空间、临时目录位于项目卷的断网验收命名空间。将所选语言的安装目录、目标 VM 及其构建收据、经审核的 VM 提交与源码树 JSON、资格入口只读挂载。线程配置还须挂载 WAT 安装目录。宿主需要 Linux Python 3.11 或更新版本及支持 Ed25519 的 `cryptography`。复制入口时保留 `debug_suite.py`、`debug_live.py`、`sysroot_suite.py` 和相邻的 `debug_fixtures/`。编译器安装目录可以位于源码检出目录之外。[隔离启动器](../../src/qualification/isolated.py) · [受测 VM 版本](../qualification/runtime-qualification.json)

另提供含三个上游 VM 文件的目录，保留它们在源码树中的相对路径。入口按 VM 提交 `454a19a3c8c1ea388472d44589a126554067ef8b` 的 SHA-256 校验协议辅助实现，并通过审核版本、构建收据及可执行文件摘要确认实际受测 VM。[调试传输](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/test/0018.debugger/run_dump_launch_policy.py) · [快照解码](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/tools/debug/snapshot.py) · [签名协议](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/test/0017.runtime/run_signed_update_boundaries.py)

以下路径均为命名空间内路径。五宿主采用同一个 `--round-id`，每次运行选择新的结果目录。

```sh
python3 -I -B /work/qa/cfamily/debug_suite.py \
  --cc-sdk /work/sdk/c --cxx-sdk /work/sdk/cpp \
  --objc-sdk /work/sdk/objc --objcpp-sdk /work/sdk/objcpp --wrwat /work/sdk/wat/bin/wrwat \
  --vm /work/host/uwvm2-ros --vm-receipt /work/host/receipt.json \
  --vm-target /work/pins/runtime-qualification.json --vm-support /work/vm-support \
  --work /work/results --round-id cfamily-acceptance-01 --jobs 2
```

x86-64 首轮可追加 `--profile wasm32-wasip1-noeh-nomte`。可用 `--language c|cpp|objc|objcpp` 和 `--capability source-debug|full-dump-restore|signed-hot-update` 选择前端与能力。单独检查 INT 调试拒绝时，显式提供 `--engine int` 及一个配置、一种语言和一项能力。跨架构运行时，`--runner-json FILE` 读取 JSON 字符串数组作为目标 ELF 的命令前缀。运行方式须支持受测 VM 对其直接父进程通道的身份验证。

## 收据和结论

每个已安装前端使用 `-O0 -g` 和选定字宽、线程、MTE、EH 组合将本语言的源码编译两次。C 和 C++ 核对两代前端构建收据。Objective-C 和 Objective-C++ 核对每个目标文件的构建注记、前端摘要、GNUstep 运行库收据和 guest 配置，再用同一前端链接通过核验的目标文件。入口记录编译、链接实参及最终模块摘要。四种语言都要从最终 Wasm 读取 DWARF 段、导出索引及函数实现索引。线程配置使用安装所得 WAT 前端生成带上限的共享内存提供模块。

- **源码调试**在执行加法的真实源码行停住，读取 `local == 40`，源码单步到同一文件的下一条标记语句，读取 `local == 42`，再续跑到正常退出。两个 Objective-C 前端的断点都设在消息派发实际调用的类方法内，Objective-C++ 方法还通过 C++ 模板读取初值。结果记录退出证据来自调试器终止回复，还是已确认续跑后通过原进程取得的退出状态。
- **完整还原**停在实际 Wasm 入口，改写四个 guest 内存字节，保存完整快照并验证其中的原始 guest 模块，再用另一个值覆盖内存。还原后须在新的停止标识下回到原先的 Wasm 位置、读回保存的四字节并正常续跑退出。快照保存在隔离结果目录中。[VM 快照契约](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/documents/runtime/unified-snapshot.md)
- **签名热更新**独立启动调试权限为 `none` 的 VM，使用认证更新流和宿主内存中的一次性 Ed25519 密钥签署启动、准备及提交。要求同一进程、同一通道、同一 nonce 上两次调用 `value()`，在世代 1 得到 17，在世代 2 得到 29。收据包含实际安装的代码摘要以及准备和 READY 阶段的测量值。[VM 生产更新契约](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/documents/runtime/production-update.md)

`inputs.json` 记录安装选择、工具摘要、测试轮次、VM 收据和命名空间标识。`build.json` 将两代 Wasm 绑定到源码、编译器及 sysroot。在每个配置、语言及引擎目录下，每项能力有独立的 `result.json`。`results.jsonl` 汇集各项观测，`summary.json` 分别统计正向能力和预期拒绝。VM 日志、原始会话和快照保存在隔离输出卷中。

`pass` 表示正向能力通过。单独点选的 INT DBG 负向断言同时要求有效认证描述符、VM 的解释器拒绝诊断以及退出码 126，满足条件时记为 `expected-rejection`。调试器若应答请求，负向断言失败。`unsupported` 记录 VM 明确返回且能识别的限制。`restore-declined` 记录已明确拒绝还原，且原停止标识和改写后的内存值均已核实。`failed` 表示出现意外结果。`build-blocked` 表示构建未能产出可运行输入。后四种结果均使入口返回非零状态。只有 `pass` 计入正向能力。
