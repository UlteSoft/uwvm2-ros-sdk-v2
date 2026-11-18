# 用 Fortran 开发 Wasm 应用

`bin/wrf` 将 Fortran 的 `PROGRAM` 编译为 Wasm 可执行文件。它接受固定格式与自由格式源码，支持有依赖顺序的模块、ISO C 互操作，以及随 SDK 编译的 Flang 数值运行库。入口为 `_start`，数据保存在模块自己的线性内存中。计算运行库支持可分配数组、指针分配和 ISO C 描述符。通用外部文件 I/O 和 coarray 程序还需要额外运行库。

## 准备编译器

若已具备审阅过的工具链和 sysroot，安装普通开发包即可。自行构建编译器时，必须在同一 SDK 提交上选择编译器源码组件。安装器会输出包含 Fortran 前端和共享构建脚本的目录。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language fortran \
  --prefix "$PREFIX" -- --component compiler-source
```

宿主机的引导工具目录需要包含能编译宿主程序的 Clang、Clang++ 和 LLD。WROS 编译器目录需要包含支持 WasmMTE 的代码生成器、链接器、`llvm-config`、LLVM 开发头文件和静态库。在 SDK 根目录执行：

```sh
python3 language/fortran/build_flang.py \
  --bootstrap "$BOOTSTRAP" --source-work "$LLVM_CACHE" --work "$FLANG_BUILD" \
  --output "$WROS_TOOLCHAIN/bin/flang"
python3 language/fortran/prepare.py \
  --toolchain "$WROS_TOOLCHAIN" --host-cxx /usr/bin/g++
```

编译配方只选择 LLVM 的 WebAssembly 后端。安装之前，它要求编译器生成两种地址宽度的 Wasm 对象，并检查生成原生 x86 对象的请求会失败。IR 辅助工具的记录绑定了源码、宿主工具和 SDK 代码生成器的摘要。这些步骤在受信任的本地构建机上执行。

Flang 构建记录绑定了上游归档、按顺序应用的代码生成器补丁和 Flang 构建补丁。假定大小数组的变量调试信息会采用所选 Wasm 目标的索引宽度。地址相关内在过程 LOC、MALLOC、SIZEOF 的整数结果跟随目标指针位宽。ISO_C_BINDING 的 C_SIZE_T 和 C_INTPTR_T 在 wasm32 上为四字节，在 wasm64 上为八字节。关闭预编译头构建时，源码会显式包含 LLVM 内建指令的完整类型声明。

## 编译应用

```fortran
program application
  use wros_scene, only: wr_abi
  implicit none
  integer :: version
  version = wr_abi()
end program
```

```sh
bin/wrf --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" \
  --target wasm32 -O3 -g application.f90 -o application.wasm
```

`wros_scene` 根据随 SDK 安装的 ROSv2 ABI 生成 Fortran 声明，显式按值传递指定宽度的 Wasm 整数。上例导入 `uwvm_ros_v2.abi`。部署时必须在 VM 中向该模块开放此接口，声明导入本身不会授予权限。

要将缓冲区地址传给 ROS 导入的 i64 参数，使用 `wros_scene` 的 `wr_address(c_loc(buffer))`。为缓冲区声明 `target`，并从 `iso_c_binding` 导入 `c_loc`。该转换保留指针的所有标签位，将 wasm32 地址按无符号值扩展至 64 位。有符号整数转换可能将第 31 位复制到高 32 位。wasm64 直接保留全部 64 位。

| 参数 | 作用 |
| --- | --- |
| `--toolchain DIR` | 指定 Wasm 编译器、链接器和 LLVM 工具目录。 |
| `--sysroots FILE` | 指定 sysroot 构建记录，可重复。选定编译器及目标配置必须恰好匹配一份记录。 |
| `--target wasm32` 或 `wasm64` | 设置地址宽度，默认为 wasm32。 |
| `--core 3.0` 或 `mvp` | 设置核心指令标准，默认为 3.0。 |
| `--eh`、`--no-eh` | 选择匹配的异常 ABI，Core 3.0 默认启用 EH。 |
| `--mte`、`--no-mte` | 整个目标默认开启内存标记；显式关闭时必须同时使用匹配的 sysroot、对象和静态库。 |
| `-pthread`、`--threads` | 选择线程配置，依赖相应的线程版 sysroot。 |
| `-O0…-O3`、`-Os`、`-Oz`、`-g` | 选择优化级别和调试符号；默认优化级别为 `-O3`。 |
| `--link-object FILE` | 链接由 SDK 编译的 Wasm 对象或静态库，可多次指定。 |
| `--flang FILE`、`--mte-tool FILE` | 指定宿主工具。Flang 必须与仅含 WebAssembly 后端的构建记录匹配。 |
| `SOURCE… -o FILE` | 按依赖顺序提供 Fortran 文件，将通过导入审核的产物写入指定路径。 |

Flang 23 没有专门控制 WasmMTE 的 Fortran 源码指令。SDK 保留 IR 上已有的 sanitizer 属性与元数据，附带的 C/C++ 数值运行库使用同一个目标配置编译。受管栈实现把能留在寄存器的值提升出去，对仍占线性栈的固定对象向 VM 登记。证明单个下标访问安全后，这块栈空间仍可能需要与物理近邻使用不同的标签。当前实现要求栈分配大小在编译时有界，并能在各条受支持的退出路径释放。对于动态栈数组和无法配对释放的非局部退出，编译器会报错。no-EH 可以编译使用固定大小局部数组并向 C 返回结果的数值过程。如果 Fortran 过程持有线性栈对象，并调用异常行为未知的外部函数，严格 no-EH 编译会拒绝。EH 配置允许编译器在异常离开该栈帧时先释放对象，再传播异常。

验证程序会在真实 VM 的解释器和 AOT 中分别执行，检查已授权与未授权的 ROS 导入、跨翻译单元数组、按引用修改标量、ISO C 类型宽度和上游数值运行库调用。反汇编检查定位在最终模块的 Fortran 函数中。[验证脚本](../../tests/fortran_aot.py)、[Fortran 测试源码](../../tests/fortran/body.f90)。

跨语言栈测试先用 C 编译器生成带 SDK 校验信息的 Wasm 对象，再将其链接进实际的 Fortran 程序。Fortran 使用 ISO C 绑定，在两个数组存活时记录其地址的整数表示，并分别读取数组元素。C 验证两者的物理距离为 16 字节，核对计算结果，并在运行时启用 MTE 时检查标签不同。测试覆盖 wasm32 和 wasm64、解释器与 AOT，以及运行时 MTE 开关。为每个待测位宽提供启用 MTE 的 sysroot 清单。默认验证 wasm32、wasm64 的 no-EH 配置。使用 `--address-width 32 --exception-model eh` 可验证 wasm32 的 EH 配置。输出目录须使用新路径。[测试命令与参数](../../tests/fortran_stack_neighbors.py)

同一测试使用 `--storage static-and-heap` 和匹配的 EH sysroot，可检查 Fortran 模块变量与两个独立的 `ALLOCATABLE` 数组。程序通过获准的 ROS ABI 查询取得数组长度，在 Fortran 中分配、逐元素赋值，将两个存活数组的地址传给 C，再在 Fortran 中释放。C 根据分配器的实际容量计算两个区域的物理间距，并在释放后读取影子标签。此用例覆盖逐元素赋值和省略 `STAT=` 的分配。下方的描述符用例覆盖整数组赋值与带状态的分配。[应用源码](../../tests/fortran/storage_neighbors.f90) · [存储检查](../../tests/fortran/storage_neighbors.c)

## 使用 xmake

按相同的完整提交号安装语言和平台，使用安装器返回的开发目录。以下命令选择宇树平台和 Fortran。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language fortran --prefix "$PREFIX"
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/unitree/fortran/development"
```

设置 `WROS_TOOLCHAIN` 和 `WROS_SYSROOTS`，将以下项目文件与 `application.f90` 放在同一目录，先执行 `xmake f -p wasm-wasip1 -a wasm32`，再执行 `xmake robot`。

```lua
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("robot")
    set_kind("binary")
    set_language("fortran")
    set_ros_platform("unitree")
    set_wros_profile({core = "3.0", mte = true, eh = true})
    set_optimize("fastest")
    set_symbols("debug")
    add_files("application.f90")
target_end()
```

多个 Fortran 源文件请按模块依赖顺序列出。安装包附有[完整项目](../../examples/fortran/xmake.lua)和[数组处理示例](../../examples/fortran/body.f90)。`add_deps` 可链接经过 SDK 校验的 C 或 C++ 静态库。运行调用 `wr_abi()` 的示例时，需要向模块开放相应查询。[xmake 参考手册](xmake.md) 说明所需环境变量、目标设置及本地运行方法。

## 数组与 C 描述符

应用可使用 `ALLOCATE(..., STAT=rc, ERRMSG=msg)`、`MOVE_ALLOC`、整数组赋值和 `DEALLOCATE(..., STAT=rc)`。前端根据输入对象引用的符号选取随附的 Flang 描述符过程，采用应用的地址宽度、异常模式和 MTE 配置编译，并与数值运行库、应用一起检查目标对象。数组库不依赖来宾文件描述符、网络套接字或环境变量。

申请内存前，运行库检查分配上下界、字节步幅及释放校验字段的大小能否用目标有符号指针范围表示。带 `STAT=` 的不可表示分配返回失败状态。零长度分配产生已分配、元素数为零的数组。C 端使用互操作头文件时，传入 `-I "$UWVM_ROS_SDK_ROOT/third-parties/fortran/flang/include"` 并包含 `"flang/ISO_Fortran_binding.h"`。

描述符测试包含 Fortran 指针别名、成功及失败的分配、错误信息、所有权转移、空数组、整数组赋值，以及 C 端独立建立的二维描述符。最终模块唯一的导入为 `uwvm_ros_v2.abi`。[测试入口](../../tests/fortran_descriptors.py) · [Fortran 应用](../../tests/fortran/descriptor_status.f90) · [C 调用](../../tests/fortran/descriptor_status.c)

## 验收本地编译器发布

默认 MTE 模式要求可信本地机构签发与目标配置匹配的发布凭据。在干净的 SDK 源码检出目录中，运行共享验收脚本并指定 `--language fortran --target wasm32 --eh -O3 -g`。若有实际完成验证的 wasm64 sysroot，也可选择 wasm64。除已批准的 SDK 提交、后端、VM 和 sysroot 摘要外，分别用 `--approved-flang-sha256` 和 `--approved-marker-sha256` 指定 `TOOLCHAIN/bin/flang` 与 `TOOLCHAIN/bin/wros-flang-mte` 的摘要。省略 `-g` 可以验收前端的普通默认配置；有无调试符号各需一份独立的发布凭据。脚本会运行双引擎和 Fortran 存储操作，并检查 Flang 能生成两种位宽的 Wasm 对象且拒绝生成原生对象。仅用于显式开发验证的 Flang 不满足发布验收条件。

Fortran 前端使用 C 和 C++ 前端构建语言运行库与 ROS 导入适配器。应为同一 VM、编译器、sysroot、`-O3 -g` 及 EH 配置生成 C、C++ 两份凭据，与 Fortran 凭据一同打包并由本地发布机构签名。生产开发环境必须配置该签名包及信任策略。[共享发布流程](../../tools/wasm/memtag/README.md) · [验收脚本](../../tools/wasm/memtag/qualify_local_c.py) · [签名安装测试](../../tests/local_release_wsea.py)

## 数组内在过程

前端检查程序、已封装目标文件和静态归档中的待解析符号。程序调用数组内在过程时，前端按选定的指针位宽、异常 ABI 和内存标签模式编译对应的 Flang 来宾运行库。包括实数和整数点积，实数、整数及逻辑矩阵乘法，带掩码或按维的求和，逻辑归约与数组重塑。仅执行标量运算的程序不编译这些源文件。

回归用例执行实数、整数矩阵乘法，验证列和、掩码和与逻辑矩阵乘积。测试核对最终链接的 Fortran 函数名，在两种 VM 引擎中运行，并检查唯一宿主导入 `uwvm_ros_v2.abi`。复数矩阵乘法及外部 Fortran I/O 仍需其他运行库组件。[Fortran 示例](../../tests/fortran/array_intrinsics.f90) · [回归测试](../../tests/fortran_intrinsics.py)

## 构建 Fortran 静态库

使用 `wrf --static` 可以将 Fortran 过程编译成客体静态库。前端给每个 Wasm 对象记录目标配置、编译器和 sysroot 的身份。库引用的 Fortran 运行时过程由最终应用链接。静态库没有部署入口。示例使用声明了 C 绑定的过程，旧式 Fortran 外部过程也可以按同样的方式链接。使用 Fortran `USE` 相互引用的源文件，应在同一目标中按模块依赖顺序编译。

```sh
wrf --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --static kernel.f90 -o filter.a
wrf --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --link-object filter.a body.f90 -o robot.wasm
```

在 Xmake 中为库目标设置 `set_kind("static")`，并在应用目标中通过 `add_deps` 添加依赖。两个目标应使用同一 SDK 提交、地址宽度、异常模型和 MTE 配置。[双目标工程](../../examples/fortran/static/xmake.lua)

静态库回归也可读取 Lite3 SDK 自带的 LAPACK 范数过程和 ROS Taskflow 发行包自带的除法过程。通过 `--dlapy3` 和 `--dladiv` 传入原文件路径，测试会核对源码摘要，并在两种 VM 引擎上检查数值结果。[静态库回归](../../tests/fortran_archives.py)

## 读取时钟

Fortran 的 `SYSTEM_CLOCK` 读取 WASIp1 单调时钟，`CPU_TIME` 读取 VM 进程消耗的 CPU 时间。应用或静态库引用这些内建例程时，前端才链接时钟适配。两者共用一个只读导入 `clock_time_get`，wasm64 模块中的导入名称为 `clock_time_get_wasm64`。部署时需开放接口，并分别授予单调时钟和进程时钟权限。进程 CPU 时间会包含同一 VM 进程内其他模块的计算。

单调时钟可用时，32 位计数以毫秒为单位，64 位计数以纳秒为单位。查询失败时，`COUNT` 返回 `-HUGE(COUNT)`，`COUNT_RATE` 和 `COUNT_MAX` 返回零。CPU 时间查询失败时返回负数。每次读取都会使用当前权限。读取仿真时间或由外部更新的 ROS 时间时，可使用 `wr_clock_read` 和对应的 ROSv2 时钟能力。[时钟回归测试](../../tests/fortran_clocks.py)
