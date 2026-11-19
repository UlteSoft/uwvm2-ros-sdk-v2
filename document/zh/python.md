# 用 Python 开发 Wasm 机器人程序

`wrpy` 将 CPython 3.14.8、Python 主程序和显式指定的模块链接为一个 WebAssembly Core 文件。目标 VM 内的解释器负责解析、导入和执行应用源码。CPython 版本与旧 SDK 一致。开发配置默认采用 wasm32、Core 3.0 和单线程，启用标准 EH 与 WasmMTE 插装。签名的 wasm64 C 站点提供 64 位对象和线性内存地址。VM 独立决定运行时的 MTE 执行方式。

## 安装与编译

将 `REV` 设置为 SDK 完整提交号，`PREFIX` 设置为安装目录，`C_SITE` 指向操作员为该提交批准的 C 工具链签名配置。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language py \
  --prefix "$PREFIX" --site-profile "$C_SITE"
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/unitree/py/development"
"$UWVM_ROS_SDK_ROOT/bin/wrpy" main.py -o robot.wasm --build-receipt
```

要开发 64 位程序，指定已签名的 wasm64 C 站点，并在安装命令末尾加上 `-- --python-target wasm64`。安装器只拉取该宽度的运行库。两个宽度并存时使用不同的安装前缀。Xmake 可执行 `xmake f -a wasm64`，直接调用编译器可传入 `--target wasm64`。

移植安装支持同一个目标选项。传入 `-- --component migration --python-target wasm64`，即可拉取 wasm64 运行库和所选平台的可编辑移植工程。

安装程序按提交、语言和平台选择文件。SDK 核对目标解释器归档、构建配方、编译器和 libc 配置的摘要。完全匹配时，修改脚本只需重新链接。其他组合从仓内固定版本的 Python.org 源码构建。冷构建在 Linux 开发机上需要 GNU Make、shell、系统 C 编译器和 binutils，并在输出目录旁创建可执行临时目录。构建过程使用同版本主机工具生成启动编码，应用程序始终在 Wasm 内执行。

| 参数 | 用途 |
| --- | --- |
| `--ros-operation NAME` | 链入一个 ROSv2 导入，可重复指定。部署时还需启用接口并授予相应资源权限。 |
| `--ros-abi` | 加入只读 ABI 查询 `wros.abi()`。 |
| `--module NAME=FILE` | 内嵌一个 UTF-8 Python 模块。包名映射到相应的 `__init__.py`，支持相对导入。上限为 256 个模块、每个文件 1 MiB、合计 4 MiB。 |
| `--target wasm32`、`--target wasm64` | 选择线性地址宽度与相应的 Python 对象布局，省略时采用签名站点配置。 |
| `--eh`、`--no-eh` | 选择匹配的 libc 配置，Python 语言异常可在两种配置中运行。 |
| `--mte`、`--no-mte` | 默认开启 MTE。手动关闭时需显式提供相应的 `--toolchain` 与 `--sysroots`。 |
| `--from-source`、`--jobs N` | 从固定源码重新构建解释器。并行数 1 至 32，默认 4。 |
| `--build-receipt` | 输出 C 后端和 Python 两份构建记录，供核查源码、解释器和最终导入。 |

Xmake 工程引入 `tools/xmake/ros.lua`，使用 `set_language("py")`、`set_ros_platform(...)` 与 `add_files("main.py")`。用 `add_wros_python_modules("robot=robot/__init__.py", "robot.math=robot/math.py")` 加入包和模块，用 `add_wros_operations("abi")` 选择宿主接口。安装目录的 `examples/py` 和 当前所选平台的 `examples/platform/<平台>/{common,extension,migration}/py` 提供示例。

## 接口和权限

基础程序导入 WASIp1 的 `clock_res_get` 和 `clock_time_get`。64 位线性内存对应的 VM 函数名带 `_wasm64` 后缀。部署者可按应用需要授予时钟权限。解释器提供 CPython 语言核心、启动所需的冻结模块及 `math`、`_struct`、`array` 等内建模块。可内嵌纯 Python 依赖。需要本机扩展、POSIX 文件、网络、动态库、进程或宿主标准流的包需要移植。应用可以通过有明确语义的 ROSv2 接口接入外部资源。解释器使用固定的内部哈希种子，安全用途的随机值须来自获授权的服务。

`wros.open(alias)` 成功时返回封装句柄，失败时返回整数状态码。`wros.close(handle)` 释放句柄。`wros.call(name, handle_or_None, request_bytes, output_capacity)` 返回状态码、响应字节或 `None`、以及写入长度。输入、输出各限 4 MiB，解释器在归还调用缓冲区前覆写其临时副本。应用持有的 Python 对象按语言本身的生命周期管理。平台子权限和上级驱动权限分别检查。

MTE 配置关闭 pymalloc、mimalloc 和解释器对象空闲列表，独立分配的对象通过带标签的 libc 分配器管理。内联字段、静态常量、解释器栈内槽位需要按其所属对象分析。迁移示例比较 ROS 1 Noetic 的 `genpy` 与 ROS 2 Jazzy 的 Fast RTPS 对 `geometry_msgs/Twist` 的真实序列化。平台测试通过观察驱动对端收到的字节数验证拒绝发生在握手前。源码和许可可在仓内查阅。[CPython 3.14.8 官方发布](https://www.python.org/downloads/release/python-3148/)

示例使用 `add_wros_tests("int", "aot")` 注册解释器和 AOT 两类测试。在示例目录设置 `WROS_VM` 为实际 VM 二进制，然后执行 `xmake build` 和 `xmake test`。平台扩展测试临时建立本机测试通道，核对父权限拒绝和子权限关闭两种情况下驱动对端收到的握手字节数均为零。
