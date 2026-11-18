# 用 Lua 开发 u2ros 应用

`bin/wrlua` 将一个 Lua 文本脚本和 Lua 5.4.9 解释器编译到同一份 WebAssembly 文件，入口为 `_start`。VM 在 guest 内解析和执行 Lua 脚本。构建机使用 Python 和 Wasm 交叉编译器，无需安装 Lua 解释器。

在 Lua 开发包目录中，将 `PRODUCER` 设置为 Wasm 专用工具链的前缀路径，将 `RECEIPT` 设置为匹配的 sysroot 构建记录。下面的示例读取 ROSv2 ABI 并在 guest 内验证中位数计算。

```sh
bin/wrlua examples/lua/body.lua --ros-abi \
  --toolchain "$PRODUCER" --sysroots "$RECEIPT" -o body.wasm
```

## 构建参数

| 参数 | 用途 |
| --- | --- |
| `SCRIPT` | 单个 Lua 文本脚本，上限为 1 MiB。输入含 NUL 或以字节码标记开头时拒绝构建。 |
| `-o FILE`、`--output FILE` | 输出 Wasm 文件。父目录须已存在。 |
| `--mte`、`--no-mte` | 默认启用内存标记，可显式关闭整个解释器和运行库的插桩。需选择匹配的 sysroot。 |
| `--toolchain DIR` | 支持 WasmMTE 的 SDK Clang 与链接器所在工具链的前缀路径。 |
| `--sysroots FILE` | 对应目标头文件和运行库的构建记录。 |
| `--target wasm32`、`--target wasm64` | guest 指针宽度，默认 wasm32。 |
| `--guest-seed UINT32` | 指定公开的 32 位无符号种子，供字符串散列、排序枢轴和数学伪随机数初始化使用。此配置不导入宿主时钟；与 `--ros-abi` 一起使用时，仅导入 `uwvm_ros_v2.abi`。伪随机序列可重复，攻击者可以预测散列种子。 |
| `--ros-abi` | 在 Lua 中注册 `wros.abi()` 并引入对应 ROSv2 接口。 |

该构建使用 Wasm Core 3.0、默认启用的 WasmMTE、单 guest 线程，通过 C++ 异常实现 Lua 的受保护调用，同时开启优化和调试符号。每次执行 `_start` 都会创建全新的 Lua 状态，其 Lua 堆活动分配上限为 16 MiB。VM 负责限制整个 Wasm 内存和执行时间。Lua 源码嵌在产物里，可以从该文件中读取。

## 库和宿主权限

脚本可以使用基础函数及 table、string、math、utf8、coroutine 库。该配置不提供文件、操作系统、包加载和 debug 库，也不提供 `dofile`、`loadfile`、`load`、`print` 和 `warn`。脚本可以用 `pcall` 捕获运行时错误。未捕获的错误和语法错误会使 guest 触发 trap。协程在同一 guest 线程中执行。

默认配置在种子初始化和排序枢轴选择时会读取 WASIp1 时钟。部署时需要对本模块暴露 `clock_time_get`，wasm64 则暴露 `clock_time_get_wasm64`。实时时钟和单调时钟可分别授权读取。单次读取被拒绝时，解释器仍能初始化种子或选择枢轴。显式指定 guest 种子后，单线程 C 库中按期限等待的备用路径也会在本地拒绝读取时钟。前端在输出 Wasm 前核对所选模式的全部导入。密钥应使用密码学随机源。

编译参数 `--ros-abi` 会增加 `uwvm_ros_v2.abi` 导入。VM 还需要把模块绑定到 scene 并开放该接口。该 Lua 配置目前支持的 ROS 操作为 ABI 查询，传感器、模型、厂商操作仍需逐项提供和验证语言绑定。

在生成了 `body.wasm` 的目录中，把 `VM` 设为支持 Core 3.0 和 SDK WasmMTE 指令的 u2ros 可执行文件，然后运行示例。

```sh
"$VM" --wasm-set-main-module-name main --runtime-int \
  --wasm-feature-enable-exceptions --wasm-feature-enable-tail-call \
  --wasm-feature-enable-simd \
  --wasip1-single-create main --wasip1-single-enable main \
  --wasip1-single-interface main clock_time_get allow \
  --wasip1-single-grant main realtime-clock \
  --ros-scene-create robot --ros-scene-bind robot main \
  --ros-scene-interface robot abi allow --run body.wasm
```
