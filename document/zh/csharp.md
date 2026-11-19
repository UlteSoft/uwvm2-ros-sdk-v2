# C# AOT 验证

独立数值回归将两个 C# 方法编译为 wasm32 核心模块，并在 uwvm2-ros 的解释器和 AOT 引擎中执行。Roslyn 生成 IL，Mono LLVMOnly 将其编译成 LLVM 位码，WasmROS LLVM 后端生成客体程序。客体无需导入宿主函数。用例分别在启用和显式关闭 MTE 时检查有符号整数计算及两个同时存活的局部变量的地址标签。

目前已经验证无需 CLR 状态的独立方法。另一个用例创建托管数组，能够生成 Wasm 目标文件；链接成客体时，链接器报告缺少真实运行库符号。使用托管对象的应用还需要面向 Wasm 的 CLR，并且垃圾回收器必须管理对象标签的完整生命周期。默认 C# 开发包安装下文的标量编译器。

## 复现

准备 Linux x86-64、Python 3.11 或以上、GNU C++、WasmROS LLVM 开发工具、兼容 Mono 输出的 llvm-extract，以及支持双引擎的 uwvm2-ros。使用 .NET SDK 9.0.100-preview.6.24328.19 和匹配的 9.0.0-preview.6.24327.7 引用程序集及 Mono WASI 运行库包。Mono LLVMOnly 交叉编译器采用 dotnet/runtime 的固定提交 573461dc897731c11d6166574b77a8c3aabba220 和 Mono LLVM SDK 16.0.5-alpha.1.24204.1。

设置下列路径变量。WROS_DOTNET 指向 .NET SDK 根目录，WROS_MONO 指向含 bin/mono-aot-cross 的编译器根目录，LLVM_EXTRACT 指向 llvm-extract 可执行文件，WROS_TOOLCHAIN 和 WROS_VM 分别指向 WasmROS LLVM 工具链根目录及 VM 可执行文件。在 SDK 根目录内运行以下命令，输出目录须为新目录。

    /usr/bin/python3 ../uwvm2-ros/tools/ros_scene/in_existing_cgroup.py \
      /usr/bin/taskset -c 4-7 /usr/bin/flock "$PWD/.tmp/sdk-qualification.lock" \
      /usr/bin/python3 -B tests/csharp_aot.py \
      --dotnet "$WROS_DOTNET" --mono-compiler "$WROS_MONO" \
      --extract "$LLVM_EXTRACT" --toolchain "$WROS_TOOLCHAIN" --runtime "$WROS_VM" \
      --output "$PWD/.tmp/csharp-methods"

测试校验固定的输入文件，逐步记录工具摘要、实际命令、运行状态和客体摘要。输出目录中的 results.json 包含本次记录。交叉编译器的源码版本和构建步骤见 [SDK1 构建配方](https://github.com/UlteSoft/uwvm2-ros-sdk/blob/466ec1647ae8577bc2c16bd4f8df8162636817f4/src/language/dotnet/mono-native-eh/README.md)。

## 受内存上限约束的 Mono 页分配

仓库收录了微软 Mono 的 WASI 页管理器和该编译单元所需的上游源码。准备 CMake、patch、WasmROS LLVM、同一编译器生成的 wasm32/EH/MTE sysroot 收据，以及支持两个执行引擎的 VM。在 SDK 根目录运行，输出须为新目录。

    /usr/bin/python3 ../uwvm2-ros/tools/ros_scene/in_existing_cgroup.py \
      /usr/bin/taskset -c 4-7 /usr/bin/flock "$PWD/.tmp/sdk-qualification.lock" \
      /usr/bin/python3 -B tests/csharp_mono_pages.py \
      --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --runtime "$WROS_VM" \
      --output "$PWD/.tmp/mono-pages"

测试验证相邻分配的标签、复制、对象退还、部分页释放和重用清零，并覆盖 VM 开启和关闭标签检查。内存固定为四页的模块会返回分配失败。还可增长两页的模块在较大的首选申请失败后，能按实际需求分配一页。诊断错误会终止测试，每个客体的宿主导入均为空。夹具显式建立对象生命周期，完整 CLR 的托管收集和对象迁移仍需验证。

## 用 wrcs 编译 C# 数值方法

安装时选择语言 `csharp` 即可获取独立整数计算开发配置。也可显式选择 `--component numeric-aot`。这个选项安装 `bin/wrcs`、IL 审核与 LLVM 源码、对应平台的 Xmake 适配和示例。在本机准备上文指定的 .NET SDK、面向 WASI 的 Mono 交叉编译器和 WasmROS LLVM 开发包，分别设置 `WROS_DOTNET`、`WROS_MONO`、`WROS_TOOLCHAIN`。GNU C++ 只编译宿主上读取 LLVM bitcode 的工具。开发者提交的 C# 代码编译为 core wasm32。

用固定入口和完整 SDK 提交号选择安装，指定本地安装前缀。

```sh
/usr/bin/python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree \
  --language csharp --prefix "$SDK_PREFIX"
export UWVM_ROS_SDK_ROOT="$SDK_PREFIX/$SDK_COMMIT/unitree/csharp/development"
```

宿主输入为 .NET SDK 9.0.100-preview.6.24328.19、版本为 9.0.0-preview.6.24327.7 的 Microsoft.NETCore.App.Ref 和 Mono WASI 包，以及根据 dotnet/runtime 提交 `573461dc897731c11d6166574b77a8c3aabba220` 构建的 LLVMOnly 交叉编译器。组件按 `language/csharp/inputs.sha256` 逐一校验后装载所需宿主文件。SDK1 提供对应版本的构建步骤。[Mono 交叉编译器构建说明](https://github.com/UlteSoft/uwvm2-ros-sdk/blob/466ec1647ae8577bc2c16bd4f8df8162636817f4/src/language/dotnet/mono-native-eh/README.md)

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrcs" --dotnet "$WROS_DOTNET" --mono-compiler "$WROS_MONO" \
  --toolchain "$WROS_TOOLCHAIN" --entry Filter.Scale \
  "$UWVM_ROS_SDK_ROOT/examples/csharp/numeric-aot/Filter.cs" -o filter.wasm
```

入口必须位于全局命名空间的非泛型静态类中，签名为 `public static int Scale(int input)`。通过 `类名.方法名` 选择入口。Wasm 导出 `evaluate(i32) -> i32`，宿主导入数量为零。支持整数常量、参数、局部变量、比较、位运算、unchecked 加减乘、分支和循环。工具读取真实 IL，按 MethodDef 行号选择 Mono 生成的方法，核对其隐藏上下文没有参与计算，再生成单参数 ABI。程序集中的类型或模块初始化器，以及入口使用托管数组、对象、其他函数调用、异常或 P/Invoke 时均会被拒绝。这些功能需要更完整的 CLR。其余方法不会成为 Wasm 入口。

默认和 `--mte` 都启用 WasmMTE 编译。发布独立内核前，`wrcs` 解码最终 Wasm，逐条验证唯一函数仅使用整数和寄存器，然后移除闲置的私有内存。最终模块没有线性内存、全局变量、宿主导入或其他执行入口。取局部变量地址的代码可能需要内存，此时证明失败。可重定位对象仍需最终链接，也无法使用这项逐制品证明。显式选用 `--legacy-mte` 会生成未签署的插装代码，`--no-mte` 关闭插装。这两个选项保留 64 KiB 私有内存。通用 CLR 堆还需单独验收。Xmake 工程可复制 `examples/csharp/numeric-aot/xmake.lua`，设置 `set_language("csharp")` 和 `add_wros_exports("Filter.Scale")`，按 `-O3 -g` 构建。调用方提供整数参数调用 `evaluate`。选择平台不会授予驱动权限。

Roslyn 生成 Portable PDB，并以 SHA-256 标识源文件。AOT 前端将方法第一个可见序列点的文档摘要与本次输入匹配，把 C# 方法名、源文件名和该行写入 DWARF。只有恰好包含一个可见序列点的方法才把指令定位到该条源码语句。包含多个序列点的方法保留方法级定位；隐藏或无法匹配的源码不生成行定位。调试信息省略构建机源文件的绝对路径。

仓库中的 `tests/csharp_source_locations.py` 分别验证单条语句、循环以及重映射文件名。使用 `tests/csharp_numeric_performance.py --help` 查看如何将已构建的 Filter.Scale 模块与独立 native C 函数对比。测试从另一 Wasm 模块调用该入口，核对全部运算的校验和，并在核心 4 上测量两种循环长度的配对耗时斜率。VTune 对两端使用硬件 Hotspots 与 Microarchitecture Exploration，记录实际可用的采样间隔和源码、汇编定位情况。

### 将数值内核链接进机器人主体

若控制器与计算内核属于同一信任域，可以在编译命令中加入 `-c --sysroots "$WROS_SYSROOTS"`，指定 `.o` 输出。产物是可重定位的 core Wasm 对象，C ABI 为 `int evaluate(int)`。编译器先验证该计算可独立链接且没有宿主导入，然后将对象绑定到匹配的编译器、sysroot 与目标配置。选择 legacy MTE 时生成未签署对象。严格构建要求经过审核的对象。最后由 SDK 的 C 或 C++ 前端审核整个主体的导入。静态链接的代码共享主体的内存和权限。

Xmake 中将 C# 内核声明为 `set_kind("static")`，设置 `add_wros_exports("Filter.Scale")` 和匹配的 `WROS_SYSROOTS`。C 主体用 `set_wros_sdk` 选择同一提交下另行安装的 C 包，使用 `add_deps` 链接静态库。仓库的 `tests/csharp_numeric.py --sysroots` 会在两种 VM 引擎运行产物。`tests/mujoco_guest.py --language csharp` 以 C# 标量计算选择仿真目标值，由获准连接驱动的 C 主体提交。

### 用 C# 程序查询 ROS 场景 ABI

复制 `examples/csharp/scene-abi`，或使用与标量示例相同的宿主工具参数执行 `wrcs --scene-entry Robot.Start`。SDK 向 Roslyn 提供 `Wros.Scene.Abi()` 声明。无参数的公开静态入口将查询结果交给同一类的公开静态整数方法，再返回该方法的结果。编译器从 IL 核对这两个调用目标，以 Mono LLVMOnly 编译实际判断逻辑。返回零表示启动成功，其他值会使客体触发陷阱。Xmake 使用 `add_wros_exports("Robot.Start")` 和 `add_wros_operations("abi")`。

最终模块仅导出 `_start`，没有线性内存，唯一导入是 `uwvm_ros_v2.abi() -> i32`。部署时 VM 必须给主模块绑定场景并暴露 ABI 查询。隐藏接口会阻止程序启动。额外的 CLR 调用或宿主操作在编译阶段被拒绝。
