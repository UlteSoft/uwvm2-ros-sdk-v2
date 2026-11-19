# 使用 F# 开发 Core Wasm 模块

`wrfs` 使用微软 .NET SDK 10.0.404 内的 F# 编译器编译 F# 10 源文件。Mono LLVMOnly 10.0.15 将生成的 CLI 方法编译为 LLVM 位码，再由 SDK 的 Wasm LLVM 工具链生成 wasm32 Core 3.0 并检查成品。目前支持独立整数函数，以及调用 u2rosv2 ABI 查询的应用。生成的模块单线程运行，无需 guest CLR、文件系统、套接字或 WASI 导入。

## 安装和编译

指定完整 SDK 提交和登记的平台。安装器会选取 F# 命令、目标平台的 xmake 适配和示例。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language fsharp --prefix "$PREFIX"
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/unitree/fsharp/development"
python3 "$UWVM_ROS_SDK_ROOT/language/csharp/prepare_host.py" --language fsharp --prefix "$HOST_TOOLS"
export WROS_DOTNET="$HOST_TOOLS/dotnet" WROS_MONO="$HOST_TOOLS/compiler"
export WROS_TOOLCHAIN=/path/to/wasm-llvm
"$UWVM_ROS_SDK_ROOT/bin/wrfs" --dotnet "$WROS_DOTNET" --mono-compiler "$WROS_MONO" \
  --toolchain "$WROS_TOOLCHAIN" --scene-entry Robot.Start \
  "$UWVM_ROS_SDK_ROOT/examples/fsharp/scene-abi/Robot.fs" -o robot.wasm
```

离线安装宿主工具时，添加 `--cache DIR`，目录中需有 `language/csharp/packages.json` 登记的三个微软原厂包。安装器验证原厂包长度和 SHA-512 摘要，提取选定的工具和引用程序集，再逐文件校验 SHA-256。LLVM 需要 Clang、wasm-ld、llvm-config 及匹配的开发库。编译方法提取器需要宿主 C++ 编译器。

## 源码与参数

使用全局 F# 模块及公开的整数策略函数。场景程序的入口将 `Wros.Scene.Abi()` 的结果交给同一模块中的策略函数。自带示例在 ABI 等于 2 时返回零，启动入口遇到非零结果会触发陷阱。VM 需授权 `uwvm_ros_v2.abi` 才能运行查询。

| 参数 | 含义 |
| --- | --- |
| `--entry Module.Method` | 编译一个接收 `int` 并返回 `int` 的 F# 函数，以 `evaluate(i32) -> i32` 导出。 |
| `--scene-entry Module.Method` | 编译一个 `unit -> int` 的入口，该入口将 `Wros.Scene.Abi()` 的返回值传给本模块的策略函数。 |
| `--mte` | 默认启用 WasmMTE 代码生成，并证明最终整数函数不依赖线性内存、其他调用或宿主导入。经过检查的场景启动器添加一个类型固定的导入。 |
| `--eh`、`--no-eh` | 选择是否启用标准 Wasm 异常代码生成特性。当前经过检查的函数不支持托管异常处理。 |
| `--no-mte` | 关闭 WasmMTE 代码生成，最终产物仍需通过同一整数函数检查。 |
| `--host-cxx PATH` | 指定编译方法提取器的宿主 C++ 编译器。 |
| `--target wasm32`、`-o FILE.wasm` | 以 `-O3 -g` 生成单个 Core Wasm 模块。 |

方法检查支持整数局部变量、算术、比较与分支。托管初始化、堆分配、数组、CLR 辅助调用、外部副作用、异常处理及 F# 脚本需要另外的运行时。构建被拒绝时，可继续使用先前成功构建的输出。编译期间对 FSharp.Core 和 .NET 类型定义的引用不会为 guest 授予宿主权限。

使用 xmake 时，将 `examples/fsharp/scene-abi` 复制到可写项目目录。保留上述四个环境变量，再执行 `xmake f -c -y -a wasm32` 和 `xmake`。通过 `add_wros_exports("Robot.Start")` 选择方法，通过 `add_wros_operations("abi")` 选择宿主操作。省略操作声明时编译独立整数函数。
