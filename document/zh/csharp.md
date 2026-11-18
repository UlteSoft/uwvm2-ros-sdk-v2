# C# AOT 验证

SDK 的测试将两个 C# 方法编译为 wasm32 核心模块，并在 uwvm2-ros 的解释器和 AOT 引擎中执行。Roslyn 生成 IL，Mono LLVMOnly 将其编译成 LLVM 位码，WasmROS LLVM 后端生成客体程序。客体无需导入宿主函数。用例分别在启用和显式关闭 MTE 时检查有符号整数计算及两个同时存活的局部变量的地址标签。

目前已经验证无需 CLR 状态的独立方法。另一个用例创建托管数组，能够生成 Wasm 目标文件；链接成客体时，链接器报告缺少真实运行库符号。使用托管对象的应用还需要面向 Wasm 的 CLR，并且垃圾回收器必须管理对象标签的完整生命周期。SDK 安装器目前拒绝 C# 开发包。

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
