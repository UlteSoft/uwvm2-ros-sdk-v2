# Rust core 应用开发

`wrrs` 将一个 Rust 2024 crate 根文件及其模块编译为 wasm32 reactor。当前配置使用 Wasm Core 3.0、单线程和 `panic=abort`，提供 `core`、编译器内建库和 SDK 的 ROS 原始导入。依赖 Cargo 包解析、过程宏、`alloc`、`std`、异常展开或 wasm64 的程序需要另外的运行库配置，当前安装包尚未提供。

## 安装与编译

安装时指定语言 `rs` 和登记了该语言的平台，例如 `unitree`。准备匹配锁定清单的 Linux x86-64 Rust 1.98.0、带开发头文件和库的 SDK LLVM 23.1.5 WasmMTE 工具链，以及符合目标配置的 sysroot 构建收据。宿主 C++ 编译器用来构建 LLVM 工具，Rust 应用和运行库都生成 Wasm 代码。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language rs --prefix "$PREFIX"
SDK="$PREFIX/$REV/unitree/rs/development"
"$SDK/bin/wrrs" app.rs --rustroot "$WROS_RUSTROOT" --toolchain "$WROS_TOOLCHAIN" \
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

启用 MTE 时，`#[unsafe(link_section = ".wros.no_memtag")]` 向编译器申请证明。当前可证明的范围为单个基本块内的整数运算、比较、选择、整数转换和标量返回。证明只接受 Wasm 标量支持的整数宽度，最多 64 位。出现指针参数、宽整数、栈对象、内存读写或调用时保留插装。后端在降级过程中继续启用插装，以保护优化或 ABI 转换新引入的存储。可变静态对象即使使用 `__wros_no_memtag_` 前缀也保留标签。构建记录分别列出获准省略和保留插装的申请。应用、ROS 绑定和运行库在 LLVM 优化前执行同一规则。安全函数可以包含 `unsafe` 块，也可以调用封装裸指针的安全接口，函数签名和 Rust 引用类型都不足以证明访问安全。完全位于寄存器的值没有需要打标签的线性内存。需要关闭整个应用的插装时显式传入 `--no-mte`。

使用 xmake 开发时设置 `set_language("rs")`，在 `add_files` 中指定 crate 根文件，并设置 `WROS_RUSTROOT`。本地 Rust 模块从该根文件声明。详见 [xmake 参考](xmake.md)。
