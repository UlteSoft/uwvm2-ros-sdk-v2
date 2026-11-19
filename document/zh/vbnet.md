# 用 Visual Basic 开发 Wasm 模块

通过 SDK 提交号安装所选平台的开发包。以下示例使用 Unitree。把安装器返回的目录设为 `UWVM_ROS_SDK_ROOT`。按[托管编译器配置](csharp.md)设置 `WROS_DOTNET`、`WROS_MONO`、`WROS_TOOLCHAIN`，分别指向经过核对的 .NET SDK、Mono LLVMOnly 编译器和 LLVM 工具链。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language vbnet --prefix "$PREFIX"
"$UWVM_ROS_SDK_ROOT/bin/wrvb" --dotnet "$WROS_DOTNET" --mono-compiler "$WROS_MONO" \
  --toolchain "$WROS_TOOLCHAIN" --scene-entry Robot.Start \
  "$UWVM_ROS_SDK_ROOT/examples/vbnet/scene-abi/Robot.vb" -o robot.wasm
```

Roslyn 将 VB 源码编译为程序集并生成可移植的 PDB，Mono AOT 生成 LLVM 位码。SDK 核对所选方法的 IL 和最终 Wasm 指令。数值入口 `--entry 类名.方法名` 导出 `evaluate(i32) -> i32`。使用全局非泛型的 `NotInheritable Class`，类中没有字段和静态初始化，公开的 `Shared Function` 接收和返回 `Integer`。支持位运算和整数比较。需要 CLR 的操作，包括需要检查溢出的整数运算，会在构建时报错。默认的 MTE 配置会验证该函数没有线性内存访问。`--no-mte` 仍使用同一个受限的方法模型。当前目标为单线程 wasm32 Core 3.0。

示例通过 `Wros.Scene.Abi()` 读取 ABI，并把结果传给同一个类中的整数策略函数。成品只导入 `uwvm_ros_v2.abi`。使用 Xmake 时，复制示例目录，执行 `xmake f -c -y -a wasm32` 和 `xmake`。项目文件使用统一的 SDK 接口声明所需操作、源码和入口方法。
