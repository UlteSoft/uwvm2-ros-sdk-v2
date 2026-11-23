# 使用 CPython 3.14.8 构建 Python 工程

Linux x86-64 版 SDK 提供 WebAssembly CPython 解释器、目标静态库和工程打包命令 `wrpy.py`。语言参数支持 `py` 和 `python`，平台可选 `unitree` 或 `generic`。应用源码在虚拟机内由 CPython 自己解析、编译并执行。宿主 Python 用于运行 SDK 工具。

## 从固定提交安装

在一个新的工程目录里执行以下命令。以下命令固定到通过下述工程实测的 Unitree Python 公开候选。安装器核对 Git 对象与 LFS 内容摘要，选择目录内同时安装 Xmake、uwvm2-ros、私有 Wasm C 后端以及离线链接应用所需的库。

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp"
export XMAKE_TMPDIR="$TMPDIR" XMAKE_GLOBALDIR="$TMPDIR/xmake-global"
revision=a524390de584d690d773ab0fe09142f0bcb4d4fd
curl -fL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --language py --platform unitree --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
```

## 用同一共享解释器运行脚本

`shared/wasm32-wasip1/core3.0-eh-mte/cpython.wasm` 是可执行的 WASI 命令。第一个脚本参数是来宾文件名，省略或指定 `-` 时从标准输入读取源码。下例的两个命令向同一安装文件传送源码，并分别选择解释和 AOT 引擎。执行快照写入当前工程目录。

```sh
cat > measure.py <<'PY'
import math
import sys

class Series(list):
    def magnitude(self):
        return math.sqrt(sum(value ** 2 for value in self))

assert sys.version_info[:3] == (3, 14, 8)
print(Series([3, 4]).magnitude())
PY
wrpy.py --run int measure.py
wrpy.py --run aot measure.py
```

本地命令逐项配置实际导入的 Preview1 接口，授予参数、标准输入输出、标准流元数据、时钟和进程退出所需权限。来宾环境为空，默认无预打开目录。此提交按来宾路径启动脚本存在已知故障。即使显式预打开只读目录，同步 MTE 下执行一个仅调用 `print` 的脚本也会以 120 退出。独立对照中关闭运行时标签后可读取该文件，从同一目录导入模块仍因目录枚举失败而报错。多文件工程可使用下方已实测的打包方式。[该提交的运行记录](../../qualification/unitree-a524390d.json)

## 在 SDK 外打包多文件工程

```sh
cp -R "$UWVM_ROS_SDK_ROOT/examples/unitree/py" my-unitree
cd my-unitree
wrpy.py --entry main.py --project-root "$PWD" --ros-operation abi --ros-operation capability.open main.py vectors.py -o direct.wasm
xmake build
xmake test -j1
```

用 `add_files` 声明所有源码，用 `set_wros_entry` 指定主文件，用 `add_wros_operations` 声明要链接的 ROS 导入。打包器将源码原始字节和包路径写入可执行模块，来宾按需编译各 Python 模块。使用点分隔的包名时一并声明上级目录的 `__init__.py`。通用示例使用 `collections.Counter`、生成器和第二个源码文件。Unitree 示例检查权限拒绝并对四个 Fast-CDR 样本执行双字节序转换。安装后的独立证明脚本可在新目录里调用共享解释器和外部 Xmake 工程。

```sh
python3 -I -B "$UWVM_ROS_SDK_ROOT/examples/unitree/py/prove.py" --sdk "$UWVM_ROS_SDK_ROOT" --work "$TMPDIR"
```

## 运行时与接口

首个目标采用非共享 wasm32 内存、Core 3.0、标准异常处理和 packed WasmMTE。`--memory64` 与 `--no-memory64` 控制运行器的语法开关，产物内存仍为 32 位。memory64 产物、共享线程、其他 Core 版本、其他优化级别、关闭 EH 或 MTE 的组合均不在本次发行配置中。此版本已从公开源码在断网环境重建。源码版和下载版均通过标准输入脚本的 INT/AOT 验证，两版解释器与目标库的摘要有差异。客体 Python 异常已实际捕获，当前模块可以在原生 Wasm EH 关闭时通过验证。

标准库包含固定源码树中选取的纯 Python 模块、CPython 内建模块和源码构建清单选中的静态扩展，例如 `math`、`_struct`、`array`、`_json` 和 `_random`。依赖缺失原生扩展的导入会抛出 Python 异常。本次构建不加载原生 wheel、宿主动态库，也不提供宿主进程能力。隔离配置忽略宿主环境变量和用户 site 目录。

`include/u2rosv2/universal/py/uwrosv2` 按域提供 163 个已注册 ROS 导入。例如 `uwrosv2.capability.wr_capability_open(memory, offset, size, output)` 保留原四个整数操作数。每个函数的英文 docstring 说明授权、线性内存使用、字段编码和返回值。`uwrosv2.Buffer` 持有可写视图并提供保留 MTE 标签的地址，直到宿主完成全部访问都须保留该对象。模块交换接口需要来宾自有且不导出的共享内存，当前单内存配置无法满足。链接导入与部署授权是两个独立步骤。供独立执行脚本的共享解释器未链接 ROS 导入。

Unitree 平台包含 `unitree_api.msg`、`unitree_go.msg` 和 `unitree_hg.msg` 共 43 个消息类。可用 `Message.from_cdr(payload)` 解码，再以 `message.to_cdr("little")` 或 `message.to_cdr("big")` 编码。支持嵌套记录、定长数组、变长序列和 UTF-8 文本。编解码器接受封装选项为零的 plain XCDRv1，默认限制为 4 MiB，可显式指定长度上限；截断、尾随数据和其他封装会被拒绝。Python 浮点转换可能改变信令 NaN 的位模式。示例覆盖 Go2 的 1,180 字节和 HG 的 2,092 字节 LowState 记录的两种端序。设备访问另需经授权的提供方。[Unitree ROS 2 v0.3.0 消息定义](https://github.com/unitreerobotics/unitree_ros2/tree/66ae09858245ac3d2231c0cc209e36a88f8d7d03/cyclonedds_ws/src/unitree)

## 从源码重建

使用当前 SDK 时，请固定同一版根安装器和 SDK 提交，以 `install.py rebuild --jobs 2` 重建所选平台的 Python 运行时。安装器读取可编辑的 3.14.8 源码，先构建同版本的宿主冻结工具，再用随 SDK 分发的 WasmMTE C 编译器和 WASI sysroot 生成目标静态库、头文件和共享解释器。宿主需要 Linux C 工具链、libc 开发头文件、GNU Make 和 CPython configure 所需的常用工具。源码锁记录了分配器 freelist 和 WASI 时钟的移植改动以及上游文件摘要。

二进制安装提供 `lib/wasm32-wasip1/cpython3.14/libpython3.14.a`。同目录收据保存旧目标库的原始编译器、闭包和内容摘要。共享命令另有独立收据，记录当前 SDK 的链接编译器、实际导入类型与模块摘要。[CPython 源码清单](../../../src/runtimes/cpython/upstream.json)
