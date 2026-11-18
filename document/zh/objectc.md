# 在 u2ros 中开发 Objective-C 程序

安装语言 ID 为 `objectc`，命令名为 `wrobjc`。它用 WebAssembly 专用 Clang 编译真正的 `.m` 翻译单元和类元数据。GNUstep libobjc2 与应用一同链接进 Wasm，负责类注册、消息查找、继承和对象分配。当前实现面向单线程、手动管理对象生命周期的程序，提供 Objective-C 运行时头文件。Foundation、ARC 和 Objective-C 异常不在当前支持范围内。

## 准备编译器和语言运行库

安装目标平台的 `objectc` 开发包及配套编译器源码包。将 `SDK` 指向 SDK 根目录，其余路径应是本地可信工具及所需 sysroot 收据的绝对路径。准备过程使用 Python、CMake、Ninja 和 patch。主机工具用于构建编译器，编译器仅包含 WebAssembly 后端。

```sh
python3 "$SDK/language/objectc/build_frontend.py" \
  --bootstrap "$HOST_LLVM" --source-work "$WORK/llvm-source" \
  --work "$WORK/objc-build" --output "$TOOLCHAIN/bin/wros-objc-clang"
python3 "$SDK/language/objectc/build_runtime.py" \
  --toolchain "$TOOLCHAIN" --sysroots "$SYSROOTS" --target wasm32 --eh --mte \
  --output "$WORK/objc32" --jobs 2
```

构建器校验仓内 GNUstep 和 robin-map 的源码摘要，写出静态库、头文件和 `runtime.json`，记录语言编译器与基础 sysroot 的身份。每种位宽、MTE 模式及 EH 配置应使用各自的输出目录。选择 EH sysroot 决定 C/C++ 链接 ABI。Objective-C 运行库在两种配置下均采用关闭语言异常的实现。

## 生成 Wasm

```sh
"$SDK/bin/wrobjc" "$SDK/examples/objectc/body.m" --target wasm32 \
  --toolchain "$TOOLCHAIN" --sysroots "$SYSROOTS" --objc-runtime "$WORK/objc32" \
  --mte --eh --reactor --export _start -O3 -g -o robot.wasm
```

默认强 MTE 需要该语言编译器、运行库、sysroot 和 VM 的已审发布记录。开发期间可显式传入 `--legacy-mte` 生成插桩程序，命令会提示尚缺严格近邻资格。关闭模式 `--no-mte` 需要对应的无插桩 sysroot 和 Objective-C 运行库。发布 Wasm 前会检查全部导入签名。用 `-c` 单独编译一个 `.m`，再将生成的 WROS 对象交给最终链接。`--reactor` 允许自定义入口，`--export` 指定导出函数，`--build-receipt` 生成构建收据。`-I`、`-D`、`--std`、`-O` 和 `-g` 分别控制包含路径、宏、标准、优化和调试信息。

`--objc-clang` 或 `WROS_OBJC_CLANG` 可选择独立准备的语言编译器，默认使用 `TOOLCHAIN/bin/wros-objc-clang`。`--objc-runtime` 或 `WROS_OBJC_RUNTIME` 指定语言运行库，默认位置为 `TOOLCHAIN/share/wros/objectc/PROFILE`，例如 `wasm32-wasip1-core3.0-eh-mte`。

## ROS、平台和权限

在 `.m` 中包含 `<wros/scene.h>` 即可使用通用 ROSv2 接口。Objective-C 方法可按部署时的别名申请能力句柄，再显式关闭。VM 对各操作独立检查权限。xmake 的平台选择使用所安装的平台描述文件。平台权限约束通用驱动调用；使用具体设备仍需父环境授权和外置驱动会话。语言运行库在 guest 内执行。

示例通过 `set_language("objectc")` 选择语言。将 `WROS_TOOLCHAIN`、`WROS_SYSROOTS`、`WROS_OBJC_RUNTIME` 指向配套构建产物。关闭 MTE 时需单独指定 `WROS_SYSROOTS_NO_MTE` 及其配套语言运行库。`tests/objectc.py` 用真实 VM 解释器及 AOT 执行继承、super、nil 消息、对象分配、权限拒绝和授权。`tests/objectc_platform.py` 对每个通用平台权限配置执行三组检查，覆盖允许连接、平台拒绝和父权限拒绝。外部测试进程只处理注册和断连，经过本地认证套接字和固定双方身份的 TLS 1.3 会话。测试记录 VM、外部进程、SDK 和模块的摘要。厂商设备协议及真实硬件需要单独验证。


## 验证默认的 MTE 配置

按照[本地签署指南](memory-qualification.md)，在固定提交的 compiler-source 工作树中使用源验证命令。选择 `--language objectc --target wasm32 -O3 -g --eh`，传入 `--objc-clang`、`--objc-runtime` 与 `--approved-objc-inputs-sha256`。最后一项是三个输入摘要组成的规范 JSON 对象的 SHA-256：`objc_frontend` 为专用编译器，`objc_runtime` 为 runtime.json，`objc_archive` 为 libobjc.a。应分别核验这些文件及底层工具链和 sysroot。语言测试在两种 VM 引擎中创建对象、传递标量消息、回收对象并检查权限。测试使用多种实例大小和相近的实际堆分配，按固定 GNUstep 版本的引用计数头核对分配范围。部署者审阅并签署输出，再按本地信任策略安装。
