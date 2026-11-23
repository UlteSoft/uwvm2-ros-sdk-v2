# TinyGo

公开候选 `b92c100d` 的默认和显式二进制安装均通过。两种安装都用随包编译器和 Xmake 构建独立工程，在随包 VM 的 INT 和 LLVM AOT 引擎运行。SDK 驱动、IR 工具和宿主工具的二进制及归档分别通过逐字节比较。从该提交下载所选源码后，原样安装程序在断网 namespace 借助独立构建的 LLVM 23.1.5 重建了 TinyGo 前端。使用公开源码构建、独立冻结源码构建及官方前端编译出的两个客体逐字节相同，均通过 INT/AOT。两次源码构建的前端 ELF 在调试行字符串表和 GNU build ID 有字节差异。 [Unitree](../../qualification/unitree-b92c100d.json)

默认二进制安装包含 `wrtg`、`prepare-ir`、经校验的官方 TinyGo 0.38.0 前端和 WASIp1 运行时，以及 Go 1.24.2。源码模式从可编辑的 TinyGo 源码、Espressif LLVM 19.1.2 和 28 个随库交付的 Go 模块编译 TinyGo 前端，并重建 SDK 原生驱动和 LLVM 23.1.5 IR 工具。源码安装解包时跳过官方 TinyGo 可执行文件。两种模式均由 SDK 提供的 Clang 和 wasm-ld 生成客体模块。[前端源码和重建命令](../../../src/compilers/tinygo/README.md)

默认是 Core 3.0、wasm32 线性内存、32 位 Go int/指针/uintptr、EH 和 MTE 开启、Wasm 线程关闭。`wrtg --print-target` 列出配置，`--go-word-bits 32` 可检查语言字长。`--memory64` 和 `--no-memory64` 选择 VM 特性，内存索引仍为 32 位。当前目标使用保守式收集器、scheduler=none 和 wasi-legacy 入口。wasm64、Wasm 线程、goroutine 调度、任意 cgo 所需的完整 C 库以及 MVP 仍需开发。

收集器按对象完整区间申领内存，应用指针保留标签，GC 元数据使用归一化偏移，扫描时读取活动标签，回收时释放整段区间。LLVM 后端为适用的栈对象和可变全局变量选择插桩。`--no-mte` 选用原有保守式分配器。`--eh` 启用 Wasm 汇编器的异常处理特性，生成模块自有的终止性 panic tag。`--no-eh` 使用上游的 panic=trap 并跳过该汇编文件。TinyGo 0.38.0 的 wasm32 目标在正常返回时执行 defer，上游尚未实现 panic 栈展开。各优化级别的 Wasm panic 运行时均直接分派到终止处理函数。[上游 recover 实现](https://github.com/tinygo-org/tinygo/blob/733a17d470870afc9c821524ce291ec5062d682b/compiler/defer.go)

源码安装需要 GNU Make、CMake、Ninja 和宿主 C/C++ 编译器。可传 `--bootstrap /absolute/llvm-prefix` 或设置 `WROS_LLVM_CONFIG=/absolute/llvm-config` 来提供 IR 工具使用的 LLVM 23.1.5 开发树。TinyGo 原生前端使用随库交付的 LLVM 19.1.2。以下命令从 GitHub 默认安装，在自己的工程目录编译并运行。

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
revision=b92c100dcb2586846797eb40ddb357764b1cd26e
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform unitree --language tinygo --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
cp -R "$UWVM_ROS_SDK_ROOT/examples/unitree/tinygo" unitree-guest
cd unitree-guest
wrtg . -o direct.wasm
xmake build
xmake test -j1
```

安装前缀包含 uwvm2-ros。可直接运行 `wrtg . -o app.wasm`。支持 `-g` 和 TinyGo 的 `-O0`、`-O1`、`-O2`、`-Os`、`-Oz`。两个编译器用相同的 go.mod、main.go、通用 ROS 导入和 Go2/HG 消息编解码器。示例从 VM 调用 ABI，以本地 LowState 数据往返编解码。启动需要时，时钟和随机数均来自实际 WASIp1 接口。在线数据需要 operator 部署 ROS 2 端点。[TinyGo 源码](https://github.com/tinygo-org/tinygo/tree/733a17d470870afc9c821524ce291ec5062d682b) [Unitree ROS 2 消息](https://github.com/unitreerobotics/unitree_ros2/tree/66ae09858245ac3d2231c0cc209e36a88f8d7d03/cyclonedds_ws/src/unitree)

## ABB ROS 1

从包含 ABB Go 模块的版本选择 `--platform abb --language tinygo`。将安装目录中的 `examples/abb/tinygo` 复制到独立工程，可运行 `wrtg . -o direct.wasm`，也可使用自带的 Xmake。示例读取场景 ABI，交换 RAPID 符号请求与响应，并编解码带 Header 的 EGM 通道状态。模块提供全部 70 种 ROS 1 正文的类型、上下行编解码器和握手 MD5。[安装、分域接口和字节边界（英文）](../../../include/u2rosv2/platform/abb/go/README.md)

## Franka ROS 2

选择 `--platform franka --language tinygo`，将 `examples/franka/tinygo` 复制到独立工程。示例读取夹爪反馈封装，并从脊柱 GetPosition 服务事件中取出 0.42 m 的响应。可使用 `wrtg . -o direct.wasm` 直接编译，也可运行当前安装自带的 Xmake。[Franka Go 与 TinyGo 手册](../../../include/u2rosv2/platform/franka/go/README.zh.md)
