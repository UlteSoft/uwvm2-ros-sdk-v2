# 标准 Go

选择 `--platform unitree --language go --mode source` 安装原生命令 `wrgo`。它使用 Go 1.24.2 的模块加载器、编译器、汇编器、链接器和标准库。源码模式用固定的 Linux x86-64 Go 引导包重建编译器、汇编器、链接器和 SDK 命令。下方固定的公开候选默认使用已验证的四个原生二进制包。旧项目的寄存器标量表达式生产器只支持 Go 语法子集，其测试记录属于旧实现。

`wrgo --print-target` 列出配置。默认启用 Core 3.0、WasmMTE 和 EH，使用 wasm32 线性内存并关闭 Wasm 线程。Go 1.24.2 的 wasm 后端使用 64 位 Go int、指针和 uintptr，指令寻址宽度为 32 位。ROS 导入单独按 VM 注册的 i32、i64 签名传参。`--go-word-bits 64` 可检查 Go 数据模型。`--memory64` 和 `--no-memory64` 选择 VM 的特性开关，生成的线性内存仍为 wasm32。标准 Go 的 32 位字长、wasm64 ABI、Wasm 线程和 MVP 仍需后端移植。

动态 goroutine 栈段由 `memtag.claimz` 取得，栈边界、栈内指针和复制路径保留标签。栈释放时先以 `memtag.release` 退役完整区间，再交回原分配器。启用 MTE 时链接器将内存上限设为 256 MiB。普通 Go 堆对象、每个独立栈帧、启动静态栈和全局变量均未实现逐对象保护。`--no-mte` 选择原有栈所有权路径。Go defer/recover 保留原有语义，`--eh` 将最终未恢复的 Go panic 转为原生 Wasm throw，`--no-eh` 走 Go 的终止路径。

在自己的目录使用 Linux x86-64、Python 3.11 以上、Git 和 curl。安装前缀自带 Xmake 和支持 INT/AOT 的 uwvm2-ros。以下命令使用已验收的公开提交。

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
revision=b92c100dcb2586846797eb40ddb357764b1cd26e
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform unitree --language go --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
cp -R "$UWVM_ROS_SDK_ROOT/examples/unitree/go" unitree-guest
cd unitree-guest
wrgo . -o direct.wasm
xmake build
xmake test -j1
```

也可直接运行 `wrgo . -o app.wasm`，调试用 `-g`，优化用 `-O0` 或 `-O2`。用户工程在 go.mod 声明两个公开模块。命令临时生成 go.work，绑定已安装包，并保留工程工作区中的其他模块和替换项。默认离线解析依赖，显式 GOPROXY 可覆盖此设置。通用接口通过 `github.com/UlteSoft/uwvm2-ros-sdk-v2/u2rosv2` 使用，Go2 消息位于 `github.com/UlteSoft/uwvm2-ros-sdk-v2/unitree/unitreego`。通用包包含 163 条真实 wasmimport，逐项给出权限、参数以及返回值约定。

外部工程调用真实 ABI，并用本地字段往返编解码完整 Go2 LowState，包括 IMU、20 个电机、BMS、数组和 CRC。实机采样需要部署侧提供序列化的 ROS 2 数据。测试启动器按成品导入配置 argv、空环境、时钟、随机数、退出、stderr 和单调时钟等待等必要权限；不挂载外部目录。默认和源码安装均已实跑；已测配置、拒绝的 ABI 与线程组合逐项记录。[Unitree 验收](../../qualification/unitree-b92c100d.json) [Go 源码](https://github.com/golang/go/tree/49860cf92a9a3ba434d2bc393faaefabe48d181e) [Unitree ROS 2 定义](https://github.com/unitreerobotics/unitree_ros2/blob/66ae09858245ac3d2231c0cc209e36a88f8d7d03/cyclonedds_ws/src/unitree/unitree_go/msg/LowState.msg)

## ABB ROS 1

从包含 ABB Go 模块的版本选择 `--platform abb --language go`。将安装目录中的 `examples/abb/go` 复制到独立工程，可运行 `wrgo . -o direct.wasm`，也可使用自带的 Xmake。示例读取场景 ABI，交换 RAPID 符号请求与响应，并编解码带 Header 的 EGM 通道状态。模块提供全部 70 种 ROS 1 正文的类型、上下行编解码器和握手 MD5。[安装、分域接口和字节边界（英文）](../../../include/u2rosv2/platform/abb/go/README.md)

## Franka ROS 2

选择 `--platform franka --language go`，将 `examples/franka/go` 复制到独立工程。示例双向转码独立的 Elbow 帧，并读取语义组件的 FrankaRobotState。解码对象独立持有关节名称和位置。可使用 `wrgo . -o direct.wasm` 直接编译，也可运行当前安装自带的 Xmake。[Franka Go 与 TinyGo 手册](../../../include/u2rosv2/platform/franka/go/README.zh.md)
