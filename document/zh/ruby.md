# 使用 wrrb 构建 Ruby 程序

SDK 把 mruby 4.0.0 和应用一起编译成一个 WebAssembly Core 模块。应用及
Ruby 核心库都在 VM 内执行，模块没有宿主文件、进程、环境变量、时钟或
套接字导入。当前配置提供嵌入式 Ruby 核心。CRuby 扩展、Rubygems、从
文件读取的 require 以及依赖系统目录的 gem 需要单独移植。构建机需要
Python 3.11 或更新版本、经签名的 C 工具链和 sysroot，以及用于生成
解释器 C++ 符号表的 /usr/bin/ruby。

选择与地址宽度匹配的签名 C 站点，启用 EH、MTE、单线程和
`-O3 -g`。用安装器返回的 directory 设置
`UWVM_ROS_SDK_ROOT`。

~~~sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --language ruby \
  --platform unitree --site-profile "$C_SITE" --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT="$PWD/sdk/$SDK_COMMIT/unitree/ruby/development"
"$UWVM_ROS_SDK_ROOT/bin/wrrb" main.rb --ros-abi --build-receipt -o robot.wasm
~~~

默认使用 Core 3.0、wasm32、单线程、标准 Wasm EH 和 WasmMTE，编译参数为
`-O3 -g`。签名的 memory64 站点选用 wasm64，也可用 `--target wasm64`
明确要求该宽度。需要关闭 MTE 时传入
`--no-mte --toolchain PATH --sysroots FILE`，并选择匹配的无插装 C/C++
sysroot。解释器处理 Ruby 异常需要标准 EH。

GC 对象各自通过带标签的 libc 分配。解析器使用堆栈，AST 节点分别分配，
由本次解析持有，解析结束时统一回收。VM 单独配置运行时的标签检查策略。
两个地址宽度均内置 mruby 多精度整数，支持宽整数字面量和算术。MTE 构建
为大整数运算的临时数据使用带标签的堆分配。

## ROS 调用与示例

每项导入都要显式指定 `--ros-operation NAME`。使用 `--ros-abi` 加入
`WROS.abi`。编译选项决定 Wasm 的导入，VM 根据部署权限决定是否允许调用。

| Ruby 方法 | 返回值 |
| --- | --- |
| `WROS.abi` | 当前 VM 暴露的 ABI 版本。 |
| `WROS.open(alias)` | 状态码和具备类型的能力句柄。 |
| `WROS.call(name, capability, bytes, capacity)` | 状态码、回复字节串或 nil，以及写入长度。 |
| `WROS.close(capability)` | 宿主状态码。成功后本地句柄失效。 |

接受零句柄的查询可传入 `nil`。请求和回复各有 4 MiB 上限。桥接代码会
复制请求，并在退出时擦除临时请求和回复缓冲区。应用接收的 Ruby 字节串
由 guest 持有。未处理的 Ruby 异常会触发陷阱，测试中的断言失败也按此报告。

每个平台都提供通用、扩展和 Noetic 移植示例。复制所选工程到可编辑的目录，
执行 `xmake build`。将 `WROS_VM` 设为可信 VM 的绝对路径，再运行
`xmake test -j1` 验证解释器和 AOT。扩展示例使用独立测试对端，检查两种
拒权结果都没有发送数据。参见[平台示例](platform-examples.md)和
[Xmake 使用说明](xmake.md)。
使用已签名的 memory64 站点构建工程时，先执行 `xmake f -a wasm64`。

源码目录的 `tests/migration/noetic_costmap_ruby.py` 可用 Noetic 原生索引函数
核对已安装的 Ruby 移植示例。提供 Ruby 移植安装目录、VM、固定版本的原版头文件和
C++ 编译器即可。探针在两种 VM 引擎中运行，且没有宿主导入。

源码目录提供官方 MuJoCo 夹具的 Go2 控制器。用同一份已签名的
Unitree SDK 安装运行
`tests/mujoco_guest.py --language ruby --installed-sdk "$UWVM_ROS_SDK_ROOT"`，
并按[仿真说明](README.md#运行外置驱动仿真)提供 VM 源码、可执行文件、
OpenSSL 和原厂模型。控制器从显式授权的 ROSv2 稳态时钟获取命令期限，
生成的 Wasm 不导入 WASI 操作。
