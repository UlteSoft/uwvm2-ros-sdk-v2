# WROS SDK v2

[English](README.md)

WROS SDK v2 把用户工程编译为在 uwvm2-ros 中运行的 Core Wasm。Linux x86-64 安装器按完整提交、语言和平台取得所选文件。[语言进度](document/zh/language-coverage.md) · [平台进度](platform/README.zh.md)

## 从当前 main 安装

在空工程目录执行。两级安装器使用同一个已发布的 SDK 提交。安装器按固定提交从官方源码构建 VM。五宿主 INT 和 AOT 验收待完成。

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp"
revision=$(git ls-remote --exit-code https://github.com/UlteSoft/uwvm2-ros-sdk-v2.git refs/heads/main | cut -f1)
curl -fsSL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform generic --language c --prefix "$PWD/sdk"
```

## 二进制发行规则

`bin/` 只收录带有 WROS 源码改动的构建产物。每个产物在 `src/` 记录上游提交、本地改动和重建输入。未修改的工具、库和 bootstrap 组件使用固定版本的官方安装地址，校验摘要后放入安装缓存。当前运行矩阵按 VM 源码提交和宿主 ELF 摘要重新验收。[宿主依赖](document/zh/host-tools.md) · [当前运行验收](document/qualification/runtime-qualification.json)

## 重现早期 Franka 安装

以下固定提交用于复现早期 SDK。当前发布的运行验收以新记录中的 VM 源码提交与实际可执行文件摘要为准。

在新工程目录准备 Python 3.11 以上、Git 和 curl。Linux x86-64 宿主需要 glibc 2.38 以上，以及系统的 libgcc、libatomic 运行库。下例通过公共 C 接口读取 Franka Elbow 消息的五组双元素字段。两项 Xmake 测试分别使用安装所得的解释器和 LLVM AOT 引擎运行实际生成的 Wasm。

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
revision=1259ec5215d7296118c1d4bdd4f1e739839adc2e
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform franka --language c --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
cp -R "$UWVM_ROS_SDK_ROOT/examples/franka/c" my-guest
cd my-guest
wrc main.c --reactor --export _start -g -o direct.wasm
xmake build
xmake test -j1
```

验收从空 HOME、空缓存开始，安装后在独立的断网 namespace 运行外部工程。父、子 cgroup 均限定 64 GiB、零 swap。执行记录核对了安装前缀中实际启动的 Xmake 和 uwvm2-ros。[验收记录](document/qualification/franka-1259ec52.json) · [宿主工具源码和构建依赖](document/zh/host-tools.md)

同一个提交也可选择 `--platform abb`，语言分别为 `c`、`cpp`、`rust`。从各自的安装前缀复制 `examples/abb/c/ros1`、`examples/abb/cpp/ros1` 或 `examples/abb/rust/ros1`，运行相同的 Xmake 命令。三种编译器均生成了实际 Wasm，并在两个引擎上通过独立 genpy 生成的 140 个报文用例。Rust 宿主需要 glibc 2.39 以上，以及提供 GLIBCXX_3.4.32 的 libstdc++。[独立 ABI 和工程结果](document/qualification/abb-1259ec52.json)

## 用标准 Go 或 TinyGo 构建 ABB ROS 1 工程

从自己的空目录开始。默认选项使用标准 Go。将下面的 `language=go` 改为 `language=tinygo` 即可用 TinyGo 在另一个目录执行同一套步骤。例程调用 VM 场景 ABI，编解码 RAPID 查询以及含 Header 的 EGM 状态数组。

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
revision=a5863c63842081570e8541fc037b43fcc52506fd
language=go
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --language "$language" --platform abb --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
cp -R "$UWVM_ROS_SDK_ROOT/examples/abb/$language" abb-guest
cd abb-guest
case "$language" in
    go) wrgo . -o direct.wasm ;;
    tinygo) wrtg . -o direct.wasm ;;
esac
xmake build
xmake test -j1
```

安装命令固定到已验证标准 Go 断网重建的版本。TinyGo 在此版本也能运行随包示例。TinyGo 从源码和二进制安装运行 140 个报文向量的结果记录在前一版本。[标准 Go 重建与完整示例](document/qualification/abb-a5863c63.json) · [两种工具链的报文结果](document/qualification/abb-28466433.json)

## Unitree Python 和 Franka Go 工具链

Unitree Python 手册给出了 CPython 3.14.8 的固定提交安装命令。默认和显式二进制选择都已用随包的 Wasm 解释器，在 INT 和 LLVM AOT 中运行外部 Python 程序。Franka Go 手册另有标准 Go、TinyGo 分别实测的冻结版本和独立构建命令。[Unitree Python](document/zh/languages/py.md) · [Franka Go 与 TinyGo](include/u2rosv2/platform/franka/go/README.zh.md) · [各版本验收记录](document/zh/qualification.md)

## 较早的 ABB C++ 候选

准备 Linux x86-64、Python 3.11 以上、Git 和 Xmake。运行 Wasm 时需要将支持 INT 与 LLVM AOT 的 uwvm2-ros 放入 PATH。在自己的工程目录执行以下命令。

以下命令只下载根安装器，选择 ABB 的 C++ 候选版本，然后在独立工程中编译 ROS 1 服务与系统状态示例。

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp"
export TMP="$TMPDIR" TEMP="$TMPDIR" XMAKE_TMPDIR="$TMPDIR"
revision=947c3067ff00cd48f3a58de9abbecec4710df69a
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --language cpp --platform abb --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export WROS_VM="$(command -v uwvm2-ros)"
cp -R "$UWVM_ROS_SDK_ROOT/examples/abb/cpp/ros1" my-guest
cd my-guest
"$UWVM_ROS_SDK_ROOT/bin/wrcc" main.cpp --reactor --export _start -g -o direct.wasm
xmake build
xmake test -j1
```

选择 `--language c` 安装 C 头文件和 wrc，选择 `--language wat` 安装汇编器。审阅目录现已包含 wasm32 和 wasm64 的 WASIp1 库，配置为 Core 3.0、EH、WasmMTE、单线程。其他目标的源码进度和已验收组合按编译器分别记录。

通用绑定位于 `include/u2rosv2/universal/<language>`。36 个专用平台的公共绑定在 `include/u2rosv2/platform/<platform>` 下，均有 C、C++、Rust、AssemblyScript、JavaScript、TypeScript 和 WAT 接口。ABB、Franka 和 Unitree 另有标准 Go 与 TinyGo 共用的 Go 模块。各平台实现的消息和字段见各自手册。选择 `generic` 可单独安装通用 ABI。C++ 的目录名为 `c++`，安装器语言 ID 为 `cpp`。[公共绑定](include/u2rosv2/) · [平台手册](platform/README.zh.md)

## 安装标准 Go 或 TinyGo

使用 ABB ROS 1 时，在含 ABB Go 模块的版本选择 `--platform abb` 和 `--language go` 或 `--language tinygo`。英文指南给出独立 guest 工程的完整构建命令，示例交换 RAPID 服务请求并读取 EGM 通道状态。[ABB Go 安装与分域接口](include/u2rosv2/platform/abb/go/README.md)

使用 Unitree 时，在新工程目录运行公开提交 `b92c100dcb2586846797eb40ddb357764b1cd26e`。标准 Go 和 TinyGo 的手册分别提供了完整的根安装器、直接编译和 Xmake 命令。两个安装选项自带 Xmake 和 VM。 [wrgo](document/zh/languages/go.md) · [wrtg](document/zh/languages/tinygo.md) · [Unitree](document/qualification/unitree-b92c100d.json)

Python 选择提供 `wrpy.py`、CPython 3.14.8 的共享 Wasm 命令及目标静态库。Unitree 另外提供 43 个 ROS 消息类及其 plain XCDR1 编解码。安装后的解释器在两种引擎均运行了外部脚本和打包后的 Unitree 工程，默认 MTE 下按来宾路径执行脚本失败。[Python 与 Unitree 工程](document/zh/languages/py.md)

## 审阅中的编译器

标准 Go 1.24.2 的 `wrgo` 与 TinyGo 0.38.0 的 `wrtg` 共享通用 Go 包和所选的 ABB、Franka 或 Unitree 消息包。两套工具链分别提供构建命令和 guest 运行用例。在当前 32 位 Wasm 线性内存目标上，两者的 Go 指针宽度分别为 64 位和 32 位。项目按语言统计时 Go 计一次。WAT 通过独立汇编器 `wrwat` 验收。C 互操作桥按使用它的语言项目验证。[标准 Go](document/zh/languages/go.md) · [TinyGo](document/zh/languages/tinygo.md) · [旧版选择项核对](document/zh/language-coverage.md)

基于 Rust 1.98.0 的原生 `wrrs` 源码可在审阅树中查看。可下载发行包和支持的目标组合按冻结提交登记。[Rust 上游与本地修改](src/compilers/rust/README.zh.md) · [各版本实际验收结果](document/zh/qualification.md)

## 源码和证据

- [安装与 Xmake 手册](document/zh/install-xmake.md)
- [37 个平台选择及只读接口](platform/README.zh.md)
- [编译器源码和构建入口](src/compilers/)
- [可链接 Wasm 库](lib/)
- [C 公共头](include/u2rosv2/universal/c/uwrosv2/scene.h)、[C++ 入口](include/u2rosv2/universal/c++/uwrosv2/scene.hpp)、[Rust crate](include/u2rosv2/universal/rust/uwrosv2/Cargo.toml)
- [VM 契约](src/abi/contract.json)及[三语导入与授权验收记录](document/qualification/bindings.json)
- [300 个 ROS 移植样本及源码摘要](src/qualification/corpus/selection.json)
- [按提交区分的验收结果](document/zh/qualification.md)
- [语言选择与移植进度](document/zh/language-coverage.md)
