# 使用 xmake 开发 Wasm 应用

## 从源文件到 robot.wasm

用完整的提交号安装所选平台和语言的开发包。安装命令返回的 `directory` 是这个选择的根目录。下面用 Unitree 平台的 C 示例生成一个调用 `uwvm_ros_v2.abi` 的模块。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language c --prefix "$PREFIX"
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/unitree/c/development"
export WROS_TOOLCHAIN="/绝对路径/wasm-toolchain"
export WROS_SYSROOTS="/绝对路径/sysroots.json"
cp -R "$UWVM_ROS_SDK_ROOT/examples/c" ./robot-project
cd robot-project
xmake f -p wasm-wasip1 -a wasm32
xmake -v robot
```

默认 release 产物位于 `build/wasm-wasip1/wasm32/release/robot.wasm`。要在本机运行这个示例，用 `WROS_VM` 指定可信的 uwvm2-ros 可执行文件，并由使用者显式开放 ABI 查询。

```sh
WROS_RUN_QUERIES=abi WROS_VM=/绝对路径/uwvm2-ros xmake run robot
```

## 项目脚本

```lua
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("robot")
    set_kind("binary")
    set_language("c")
    set_ros_platform("unitree")
    set_wros_profile({core = "3.0", mte = true, eh = true, std = "c17"})
    set_optimize("fastest")
    set_symbols("debug")
    add_files("body.c")
target_end()
```

### SDK 控制函数

| 函数 | 参数、范围及行为 |
| --- | --- |
| `set_language(id)` | 为当前目标选择语言标识。配置时检查安装位置、适配器和前端程序。 |
| `set_ros_platform(id)` | 为目标选择具体厂商或平台。平台适配器必须登记该语言。设备权限由部署时的策略决定。 |
| `set_wros_sdk(directory)` | 为单个目标指定另一次安装返回的 `development` 或 `compiler-source` 目录，提交必须与公共入口一致。一个项目可包含不同语言、不同平台的目标。 |
| `set_wros_profile(table)` | 设置下面列出的一个或多个字段，作用域是当前目标。未知字段在配置阶段报错。 |
| `add_wros_exports(name, ...)` | 在 C/C++ 应用的 `_start` 之外额外导出 Wasm 函数。名称须满足编译前端的 C 标识符规则。 |

| 配置字段 | 类型与默认值 | 语义 |
| --- | --- | --- |
| `core` | 字符串，默认 `"3.0"` | 可选 `"3.0"` 或 `"mvp"`。MVP 基线使用 wasm32、单线程并关闭 EH。MTE 由同一目标的 mte 字段决定。 |
| `mte` | 布尔，默认 true | 设为 false 可显式关闭整个目标的 MTE。目标文件和静态库须匹配该编译配置及 sysroot。C/C++ 源码属性仍可改变局部插桩。 |
| `eh` | 布尔，Core 3.0 默认 true | 选择匹配的异常运行时。MVP 默认 false。 |
| `std` | 可选字符串 | C 支持 `c11`、`c17`、`c23`。C++ 支持 `c++17`、`c++20`、`c++23`。 |
| `lua_abi` | 布尔，默认 false | 在 Lua 中提供 `wros.abi()`。部署或运行时仍须显式开放该查询。 |

### xmake 内置构建接口

| 接口 | 对 Wasm 项目的作用 |
| --- | --- |
| `target(name)`、`target_end()` | 定义应用或库的目标范围。 |
| `set_kind("binary")` | 生成 Wasm 模块。C/C++ 使用 reactor 链接方式并导出 `_start`。 |
| `set_kind("static")` | 将 C/C++ 源文件编译为 SDK 校验过的 Wasm 目标文件，打包生成可复现的静态库。静态库目标目前只接受源文件。 |
| `add_files(...)` | C 接受 `.c`，C++ 接受 `.cpp`、`.cc`、`.cxx`、`.C`。链接应用时也接受经 SDK 校验的 `.o` 和 `.a`。Lua 目标接受一个 `.lua` 文件。 |
| `add_deps(name, ...)` | C/C++ 应用链接 SDK 静态库目标，链接时检查编译器摘要和目标配置。 |
| `set_plat(id)`、`xmake f -p id` | 默认 `wasm-wasip1`。使用 `wasm-wasip1-threads` 时需要匹配的线程工具链与 sysroot。 |
| `set_arch(id)`、`xmake f -a id` | 选择 `wasm32`（默认）或 `wasm64`。项目希望保留命令行选择时可用 `get_config("arch")`。 |
| `add_includedirs(...)`、`add_defines(...)` | 向 C/C++ 前端传入包含目录和对象式宏定义。 |
| `set_optimize(level)` | C/C++ 的 `none`、`fast`、`faster`、`fastest`、`smallest` 依次对应 `-O0`、`-O1`、`-O2`（默认）、`-O3`、`-Os`。 |
| `set_symbols("debug")` | C/C++ 启用调试符号。结合 `set_optimize("fastest")` 可进行源码级性能定位。 |
| `set_filename(name)`、`set_targetdir(directory)` | 指定产物名称或位置。应用后缀为 `.wasm`，静态库后缀为 `.a`。 |
| `includes(...)`、`path.join(...)`、`os.getenv(...)` | 加载公共声明，拼接路径并取得使用者指定的 SDK 安装位置。 |

SDK 目标拒绝透传原始编译或链接参数、宿主软件包、宿主库目录及 framework。开发机上的构建脚本具备开发者的权限，VM 在应用运行时执行授权检查。所有上游声明函数、内置脚本模块和扩展模块可按名称查阅参数、返回值及示例。[xmake 上游 API 索引](xmake-api-index.md)

### 工具、语言配置和本地运行

| 环境变量 | 用途 |
| --- | --- |
| `UWVM_ROS_SDK_ROOT` | 含公共 xmake 入口的 SDK 安装目录。 |
| `WROS_PLATFORM` | 随包 C 示例的目标平台，默认 `unitree`。其他项目可以直接调用 `set_ros_platform`。 |
| `WROS_TOOLCHAIN`、`WROS_SYSROOTS` | C/C++ 与 Lua 构建所需的工具链目录和 sysroot 构建记录。缺少匹配的配置时编译失败。 |
| `WROS_SYSROOTS_NO_MTE` | 可指定关闭 MTE 的目标使用的构建记录。省略时 WROS_SYSROOTS 必须包含该配置。 |
| `WROS_VM` | `xmake run` 使用的可信 uwvm2-ros 绝对路径。 |
| `WROS_RUN_QUERIES` | 逗号分隔的本地测试授权，默认空。可选 `abi`、`realtime-clock`、`monotonic-clock`、`realtime-resolution` 和 `monotonic-resolution`。完整部署策略由部署器或 VM 命令行指定。 |

Lua 编译配置为 Core 3.0、单线程、可选 MTE、EH、`-O3 -g`。TinyGo 适配器将 Go 模块及其保守式垃圾收集器编为 wasm32。数值 Fortran 适配器支持 wasm32 与 wasm64。标准 Go 有独立的编译器和运行库。缺少工具链、sysroot、适配器或最终导入检查失败都会终止构建。平台清单的登记本身不能用于编译。

### 按需安装和适配器目录

开发包包含公共入口、`platform/<平台>/xmake/platform.lua` 和 `language/<语言>/xmake/adapter.lua`。安装脚本在下载载荷前检查平台与语言组合，逐个校验选择的文件及摘要，相同文件复用缓存。协议和原始绑定可独立安装。多目标项目先安装所需组合，再用每个目标自己的 `set_wros_sdk` 指向相应安装目录。

平台适配器的 `describe()` 返回 `id`、`languages`、`admission`。语言适配器的 `describe()` 返回 `id`、`program`、`extensions`。C 系列使用公共构建器。其他语言可在 `validate(target, request)` 校验配置，在 `build(target, request, sources)` 调用对应前端。入口会先核对安装选择，再调用这些函数。公共代码负责产物命名，本机测试由 VM 执行。

### TinyGo 和数值 Fortran

TinyGo 主模块使用 `set_language("tinygo")` 和 `add_files("go.mod")`。通过 `WROS_GOROOT` 与 `WROS_TINYGOROOT` 指定已校验的 Go、TinyGo 发布包。可用 `WROS_HOST_CXX` 指定构建 LLVM 辅助工具所需的宿主 C++ 编译器。来宾使用 wasm32、Core 3.0、单线程和 `-O3 -g`。[TinyGo 开发指南](tinygo.md)

数值 Fortran 程序使用 `set_language("fortran")` 并添加 Fortran 源文件。前端默认使用工具链内的 `bin/flang` 和 `bin/wros-flang-mte`，也可用 `WROS_FLANG` 与 `WROS_FLANG_MTE_TOOL` 显式指定已校验的工具。通过 `add_deps` 关联经过 SDK 校验的 Wasm 静态库。xmake 适配器支持 Core 3.0、两种位宽与两种 EH 模式，来宾使用单线程。每个目标使用所选的 MTE 配置。[Fortran 开发指南](fortran.md)

### Rust no_std

Rust 目标使用 `set_language("rs")`，并通过 `add_files("src/lib.rs")` 指定一个 crate 根文件。将 `WROS_RUSTROOT` 设为固定版本 Rust 的宿主工具链目录。默认使用 wasm32 Core 3.0、panic=abort、单线程和 MTE。关闭插桩时设置 `set_wros_profile({mte=false})`，并通过 `WROS_SYSROOTS_NO_MTE` 指定匹配的收据。支持从 none 到 fastest 的优化级别和调试符号。参见 [Rust 开发指南](rust.md)。
