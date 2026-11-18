# Rust core 应用开发

`wrrust` 将一个 Rust 2024 crate 根文件及其模块编译为 wasm32 reactor。当前配置使用 Wasm Core 3.0、单线程和 `panic=abort`，提供 `core`、编译器内建库和 SDK 的 ROS 原始导入。依赖 Cargo 包解析、过程宏、`alloc`、`std`、异常展开或 wasm64 的程序需要另外的运行库配置，当前安装包尚未提供。

## 安装与编译

安装时指定语言 `rs` 和登记了该语言的平台，例如 `unitree`。准备匹配锁定清单的 Linux x86-64 Rust 1.98.0、带开发头文件和库的 SDK LLVM 23.1.5 WasmMTE 工具链，以及符合目标配置的 sysroot 构建收据。宿主 C++ 编译器用来构建 LLVM 工具，Rust 应用和运行库都生成 Wasm 代码。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language rs --prefix "$PREFIX"
SDK="$PREFIX/$REV/unitree/rs/development"
"$SDK/bin/wrrust" app.rs --rustroot "$WROS_RUSTROOT" --toolchain "$WROS_TOOLCHAIN" \
  --sysroots "$WROS_SYSROOTS" --no-eh -O3 -g -o robot.wasm
```

下面的 `app.rs` 使用预先声明的 `wros_scene` crate。运行时需要在 VM 策略中授予此示例使用的 ABI 查询权限。

```rust
#![no_std]

#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    let version = unsafe { wros_scene::wr_abi() };
    assert_eq!(version, 2);
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    core::arch::wasm32::unreachable()
}
```

## 编译选项

| 选项 | 用途 |
| --- | --- |
| `--rustroot PATH` | 指定与 `language/rust/toolchain-inputs.json` 对应的 Linux x86-64 Rust 1.98.0。 |
| `--toolchain PATH` | 指定 WasmMTE Clang、链接器和相应 LLVM 开发文件。 |
| `--sysroots FILE` | 选择匹配的 sysroot 收据，可重复传入不同配置。 |
| `--target wasm32 --core 3.0 --no-eh` | 当前支持的目标，也是此 Rust 前端的默认配置。 |
| `--mte`、`--no-mte` | 为所有 crate 和最终 sysroot 选择统一的插桩配置，默认启用 MTE。 |
| `-O0`、`-O1`、`-O2`、`-O3` | 在确定插桩策略后使用指定的 LLVM 优化级别，默认 `-O2`。 |
| `-g` | 为 guest 代码保留源码位置信息。 |
| `--host-cxx FILE` | 选择构建 LLVM IR 工具的宿主 C++ 编译器，默认 `/usr/bin/c++`。 |
| `--print-identity` | 输出目标配置、编译器和源码摘要、各 crate 的 IR 与对象摘要以及局部关闭插桩的声明清单。 |
| `-o FILE.wasm` | 链接并完成导入审查后发布最终模块。 |

前端每次从仓内固定版本的上游 `rust-src` 重建 `core` 和 `compiler_builtins`，在独立的临时 sysroot 中保存 Rust 元数据。先关闭 MIR 优化，在应用源码的插桩选择后再启用 LLVM 优化。运行库构建所需的内部选项由前端固定。用户 crate 使用稳定 Rust 语法。最终模块会检查每项导入的模块名、函数名和签名。

按函数关闭插桩可同时使用 `#[unsafe(link_section = ".wros.no_memtag")]` 和 `#[inline(never)]`。可变静态变量使用显式符号名，例如 `#[unsafe(export_name = "__wros_no_memtag_state")]`。在 Wasm 目标上，Rust 将静态变量的 `link_section` 编译为自定义节内的数据，无法用它标识需要处理的全局变量。标记函数在后续优化中保留调用边界，同时要求 `#[inline(always)]` 会产生错误。有界访问还可以由编译器的静态证明单独省略标签。运行环境中的 VM 检查策略由部署者配置。

使用 xmake 开发时设置 `set_language("rs")`，在 `add_files` 中指定 crate 根文件，并设置 `WROS_RUSTROOT`。本地 Rust 模块从该根文件声明。详见 [xmake 参考](xmake.md)。
