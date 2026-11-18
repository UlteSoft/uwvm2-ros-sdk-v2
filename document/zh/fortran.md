# 用 Fortran 开发 Wasm 应用

`bin/wrfortran` 将 Fortran 的 `PROGRAM` 编译为 Wasm 可执行文件。它接受固定格式与自由格式源码，支持有依赖顺序的模块、ISO C 互操作，以及随 SDK 编译的 Flang 数值运行库。入口为 `_start`，数据保存在模块自己的线性内存中。当前还缺少通用外部文件 I/O、coarray 和依赖完整描述符运行库的功能。

## 准备编译器

宿主机的引导工具目录需要包含能编译宿主程序的 Clang、Clang++ 和 LLD。WROS 编译器目录需要包含支持 WasmMTE 的代码生成器、链接器、`llvm-config`、LLVM 开发头文件和静态库。在 SDK 根目录执行：

```sh
python3 language/fortran/build_flang.py \
  --bootstrap "$BOOTSTRAP" --source-work "$LLVM_CACHE" --work "$FLANG_BUILD" \
  --output "$WROS_TOOLCHAIN/bin/flang"
python3 language/fortran/prepare.py \
  --toolchain "$WROS_TOOLCHAIN" --host-cxx /usr/bin/g++
```

编译配方只选择 LLVM 的 WebAssembly 后端。安装之前，它要求编译器生成两种地址宽度的 Wasm 对象，并检查生成原生 x86 对象的请求会失败。IR 辅助工具的记录绑定了源码、宿主工具和 SDK 代码生成器的摘要。这些步骤在受信任的本地构建机上执行。

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
bin/wrfortran --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" \
  --target wasm32 -O3 -g application.f90 -o application.wasm
```

`wros_scene` 根据随 SDK 安装的 ROSv2 ABI 生成 Fortran 声明，显式按值传递指定宽度的 Wasm 整数。上例导入 `uwvm_ros_v2.abi`。部署时必须在 VM 中向该模块开放此接口，声明导入本身不会授予权限。

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
| `--flang FILE`、`--mte-tool FILE` | 指定宿主工具。验证流程允许显式选取一个固定摘要的开发版 Flang。 |
| `SOURCE… -o FILE` | 按依赖顺序提供 Fortran 文件，将通过导入审核的产物写入指定路径。 |

Flang 23 没有专门控制 WasmMTE 的 Fortran 源码指令。SDK 保留 IR 上已有的 sanitizer 属性与元数据，编译器可以根据安全证明优化标记操作。附带的 C/C++ 数值运行库使用同一个目标配置编译。

验证程序会在真实 VM 的解释器和 AOT 中分别执行，检查已授权与未授权的 ROS 导入、跨翻译单元数组、按引用修改标量、ISO C 类型宽度和上游数值运行库调用。反汇编检查定位在最终模块的 Fortran 函数中。[验证脚本](../../tests/fortran_aot.py)、[Fortran 测试源码](../../tests/fortran/body.f90)。
