# 使用 TinyGo 开发机器人应用

`wrtg` 将本地 Go 模块编译为单个 wasm32 命令模块，内置保守式垃圾回收器。开发机为 Linux x86-64，客户程序使用 WebAssembly Core 3.0、一个线性内存和一个执行线程。下例的应用入口为 `_start`。应用需要的 ROS 和时钟操作由 VM 操作员分别授权。

## 准备编译环境

安装 SDK 的 TinyGo 开发包。选择 SDK 打过补丁的 LLVM 23.1.5 开发构建，以及与目标地址宽度、异常和 MTE 模式匹配的 sysroot 构建记录。保留 `bin/llvm-config` 引用的 LLVM 源码头文件、生成头文件和库。SDK 用这些文件在宿主上编译小型 IR 处理工具。宿主 C++ 编译器必须兼容 LLVM 库的宿主 ABI。

获取下列 Linux x86-64 发行包，先校验整个压缩包的 SHA-256，再解压到受信任的构建目录。

| 路径变量 | 发行包 | SHA-256 |
| --- | --- | --- |
| `GO_ROOT` | [Go 1.24.2](https://go.dev/dl/go1.24.2.linux-amd64.tar.gz) | `68097bd680839cbc9d464a0edce4f7c333975e27a90246890e9f1078c7e702ad` |
| `TINYGO_ROOT` | [TinyGo 0.38.0](https://github.com/tinygo-org/tinygo/releases/download/v0.38.0/tinygo0.38.0.linux-amd64.tar.gz) | `edc3476ec69e309f0fd4afc1ec79c34e00a14bc3848a7133ac53f814e72faebd` |

两个变量分别指向包含 `bin` 的目录。每次构建都会核验参与构建的 Go、TinyGo 组件的文件清单及 SHA-256，然后将这些组件与 SDK 的运行时源码映射到私有构建目录。整个构建期间，编译器、LLVM、sysroot 和构建记录均应由受信任的构建用户管理。项目的依赖须在本地可解析。编译器从空模块缓存开始，读取项目的 `go.mod`，关闭网络取包和自动工具链更新。

## 编写并构建程序

在一个新目录中将 `SDK` 设为安装目录的绝对路径，创建两个文件。

```sh
cat > go.mod <<EOF_MOD
module example.local/robot

go 1.24

require wros.local/scene v0.0.0
replace wros.local/scene => "$SDK/language/tinygo/scene"
EOF_MOD

cat > main.go <<'EOF_GO'
package main

import "wros.local/scene"

func main() {
    if scene.Abi() != 2 { panic("unexpected ROS guest ABI") }
}
EOF_GO

"$SDK/bin/wrtg" . -o body.wasm \
    --goroot "$GO_ROOT" --tinygoroot "$TINYGO_ROOT" \
    --toolchain "$WROS_LLVM" --sysroots "$SYSROOT_RECEIPT" \
    --host-cxx /usr/bin/c++ --print-identity
```

本例只导入 `uwvm_ros_v2.abi`，无需开启 WASIp1。`wros.local/scene` 提供与 SDK ABI 数值宽度一致的底层声明，包含 64 位缓冲区参数。需要客户内存地址时应传完整的带标签指针，VM 会检查调用者的授权。

| 参数 | 用途 |
| --- | --- |
| `PROJECT`、`-o FILE.wasm` | 输入包含 `go.mod` 和 `package main` 的目录，通过导入审查后原子替换输出文件。 |
| `--goroot`、`--tinygoroot` | 指定两个已锁定版本的宿主发行包。 |
| `--toolchain`、`--sysroots` | 指定打过补丁的 LLVM 和匹配的 sysroot 构建记录。多个配置可多次提供 `--sysroots`。 |
| `--host-cxx` | 指定构建宿主 IR 工具的 C++ 编译器，默认使用系统二进制目录下的 `c++`。 |
| `--target wasm32`、`--core 3.0` | 选择受支持的客户地址宽度和标准级别。其他宽度、级别和线程参数会报错。 |
| `--mte`、`--no-mte` | 默认给客户对象使用 MTE。显式关闭时选用另一套 sysroot 和上游未插桩垃圾回收器。可用的 Go 构建标签分别为 `wros_mte` 和 `wros_nomte`。 |
| `--eh`、`--no-eh` | 选择启用或关闭 EH 的 C sysroot，默认启用。两种配置中未处理的 Go panic 都会触发 trap。 |
| `--print-identity` | 输出 JSON，包含 sysroot 标识，以及编译器工具、IR 工具、运行时、各阶段产物和最终模块的 SHA-256。 |

TinyGo 将应用和 Go 运行时编入 LLVM bitcode。SDK 为有实现的函数和可变全局变量设置 MTE 属性，同时保留 IR 中显式关闭 sanitizer 的标记。要关闭某一函数栈或某个全局变量的插桩，可使用 `//go:section .wros.no_memtag`。用于函数时，所在包须导入 `unsafe`。TinyGo 会保留函数边界，SDK 在生成机器码前消费段标记。外部调用、分配器和其他带标签对象各自遵循原有规则。此约定采用 TinyGo 已有的段指令。[TinyGo 源码](https://github.com/tinygo-org/tinygo/blob/v0.38.0/compiler/symbol.go)

LLVM 后端使用 `-O3 -g` 编译，并按静态证明省略部分安全栈访问的插桩。启用 MTE 时，垃圾回收器按 16 字节粒度分配、清零并记录标签，在扫描时验证带标签的根引用，在清扫时清除数据及影子标签。wasm32 软件 MTE 使用 4 位标签。客户线性内存上限为 256 MiB，链接时为栈预留 32 KiB。VM 运行时是否检查标签与编译时选择哪套回收器是两个独立选项。

此配置关闭 goroutine 调度器。等待、消息和设备访问使用显式授权的 ROS 接口。运行时的命令参数为空，无控制台。读取实时时钟与单调时钟时使用可审计的 WASIp1 时钟接口。供哈希表使用的非密码学种子不依赖宿主熵源。密码学熵源、描述符、套接字和其他 POSIX 导入受最终白名单约束。编译被拒时保留上次生成的文件。

运行时回归程序检查堆内存复用、分配清零、链表跨回收存活、对象标签和实际回收数量。VM 测试分别覆盖两个执行引擎、ROS 授权与拒绝以及 MTE 扩展语法。验证范围限定于上述宿主发行包和客户配置。

## 安装签名的 TinyGo 开发环境

将经过审核的 Go 和 TinyGo 发行版根目录放在 `TOOLCHAIN/libexec/wros/go` 和
`TOOLCHAIN/libexec/wros/tinygo`，将编译 LLVM 标记工具所用的本机 C++ 编译器
放在 `TOOLCHAIN/libexec/wros/host-cxx`。这些路径可以链接到本机安装。
通过 `tools/wasm/memtag/qualify_local_c.py --language tinygo` 对选定的工具链、
VM 和 sysroot 做验收。用 `--approved-tinygo-inputs-sha256` 指定包含 `go`、
`tinygo`、`host_cxx` 三个二进制 SHA-256 的规范 JSON 对象的 SHA-256。
每次验收覆盖一个单线程 wasm32 配置，优化级别为 `-O3 -g`。EH 和 no-EH 分别验收。

按照站点的 WSEA 策略签署验收声明。安装时选择 `--language tinygo` 和
`--site-profile /绝对路径/site.json`。项目配置上述 Go 模块引用后，
执行 `wrtg PROJECT -o controller.wasm --build-receipt` 即可构建。
Xmake 可以直接使用该安装提供的工具路径。编译器在构建前校验工具链各组件。
签名声明或经过度量的编译器输入发生变化后，需要重新审核。
