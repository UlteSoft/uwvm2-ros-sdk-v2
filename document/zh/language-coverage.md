# 按旧版选择项核对语言覆盖

v1 提交 `466ec1647ae8577bc2c16bd4f8df8162636817f4` 有 29 个选择 ID，其中包含一个 C 互操作桥。下面的源码位置除标为 v1 的条目外，均指旧 v2 基线 `476799fc80b1ebeea82721a82d658dee75fce9a6`。每项分别记录新 SDK 实际进度，完整发布资格另行验收。[按冻结提交保存的验收证据](qualification.md)

[ABB 安装与运行实测记录](../qualification/abb-36c098e8.json)

- **AssemblyScript** (`as`). 163 项原始导入核对通过，38 个分域入口已编译。ABB 的安装和位置示例在另行提供 Node.js 22.22.3 后通过 INT/AOT，该项宿主依赖在早期公开候选 `36c098e8` 中需要另行提供。候选 `947c3067` 已随包提供固定版本的 Node 可执行文件。
- **C** (`c`). wrc 已真实链接 wasm32 和 wasm64，均运行过 INT/AOT。其他配置待验。 `language/c`
- **C FFI bridge** (`c_ffi_bridge`). v1 的 Swift、Haskell、Nim、D 和 Odin 绑定通过 C ABI 调用原始 Wasm 导入。v2 的 QuickJS 使用自己的 C 适配层。ABB 的进程记录确认构建 JavaScript 客体时启动了随包的私有 C 编译器。桥按使用方作为依赖验证，每种使用语言单独编译、运行，语言数量单独统计。旧桥位于 `v1: src/platform/ros/c_ffi_bridge/shim.c`。[QuickJS 适配层](../../src/compilers/js/entry.c) · [ABB 实测](../qualification/abb-28466433.json)
- **C++** (`cpp`). wrcc 已实际编译 C++98 至 C++26；标准、所有权和两种 ABI 各自有运行记录。 `language/cpp`
- **C#** (`csharp`). 已合入 .NET Runtime 10.0.15 的 Mono AOT 与 WASI 运行时源码以及旧版的 SGen 有界排序修改。Roslyn、配套发行物和 C# 客体工程仍待验收。[Mono 源码和修改](../../src/runtimes/dotnet/README.zh.md)
- **D** (`d`). LDC v1.41.0 前端、druntime 和固定提交的 Phobos 已移入，保留旧版 BetterC 客体入口。公开编译器及厂商工程待验收。[源码](../../src/compilers/d/README.zh.md)
- **Fortran** (`fortran`). 已合入 LLVM 23.1.5 的 Flang、MLIR、旧工作区的 Wasm ABI、C 描述符及 MTE IR 适配。可安装的编译器和各目标配置仍待独立验收。[Fortran 前端与运行时](../../src/compilers/fortran/README.zh.md)
- **F#** (`fsharp`). 旧版数值型 AOT 组件待迁入和复验。 `install/packages/fsharp/numeric.json`
- **Go** (`go`). Unitree 的默认、显式二进制和源码安装均用 `wrgo` 构建了独立 Go 工程，INT/AOT 均通过。标准 Go 的四个宿主工具逐字节一致。 [Unitree](../qualification/unitree-b92c100d.json)
- **Haskell** (`haskell`). 待迁入并验证 Haskell 编译器及其 Wasm 运行时闭包。 `v1: install/catalog.json`
- **Java**（`java`）。通用与 ABB 选择使用原生 `wrjava`、OpenJDK 21、修改过的 TeaVM 0.13.1 以及 WROS C 链接工具。五种 Linux 宿主各有 WROS 原生入口包，JDK 来自锁定的上游发行版。独立安装、客户程序运行与源码重建尚待验收。[安装方法和范围](languages/java.md)
- **JavaScript** (`js`). 从 GitHub 安装的 QuickJS 前端已在断网工程编译 ABB 位置示例，并通过 INT/AOT。产物仅导入 Preview 1 时钟。
- **Kotlin** (`kotlin`). TeaVM 后端接收 Kotlin/JVM 字节码。kotlinc 发行包、guest 库及从新安装编译运行的 Kotlin 工程待验收。[后端源码](../../src/compilers/jvm/README.zh.md)
- **Lua** (`lua`). Lua 5.4.9 的可编辑源码已放入审阅树，带 MTE 的解释器及安装后的用户脚本仍待验收。[Lua 源码与提交](../../src/runtimes/lua/upstream.json)
- **MoonBit** (`moonbit`). 待整合语言编译器并用实际 MoonBit 工程验收。 `v1: install/catalog.json`
- **Nim** (`nim`). 已迁入 Nim 2.2.4 前端、Linux x86-64 C 引导源码、Wasm 目标选择和 guest 入口。公开安装和独立 Nim 工程运行待验收。[源码与构建步骤](../../src/compilers/nim/README.zh.md)
- **Objective-C** (`objectc`). 已有 LLVM 23.1.5 的 GNUstep 驱动与 nil 消息返回值处理代码，以及合入 Wasm 移植的 libobjc2 v2.3 和 robin-map v1.4.0。实际安装和编译运行 Objective-C 用户工程待验收。[Objective-C 源码](../../src/compilers/objc/README.zh.md)
- **Odin** (`odin`). 官方月度发行的前端、基础运行时和 core 标准库已移入，17 个文件合入 freestanding wasm64 移植。公开安装、用户工程和 VM 运行待验收。[源码和修改](../../src/compilers/odin/README.zh.md)
- **PHP** (`php`). 已移入 PHP 8.4.13 的 Zend、嵌入入口和三项 WASI 适配。可安装解释器和用户工程待验收。[源码与修改](../../src/runtimes/php/README.zh.md)
- **Python**（`py`、`python`）。已链接 CPython 3.14.8 的 wasm32 WasmMTE 共享解释器。安装选择提供静态库、源码重建和外部 Unitree 工程。默认、显式二进制与断网源码重建均在外部工程通过 INT/AOT。按来宾路径执行脚本在默认 MTE 下失败。[Python 工程](languages/py.md)
- **R** (`r`). R 4.5.1 的求值器、base 与数学库源码已移入，合入两项 Wasm 移植修改。可安装解释器和用户工程待验收。[源码与修改](../../src/runtimes/r/README.zh.md)
- **Rust** (`rs`). ABB 公开候选 ba811556362cf721bda0a27b8469e6da73d436aa 已默认安装原生 wrrs。其 wasm32、wasm64 guest 各匹配全部 163 个导入，并已在 INT 和 LLVM AOT 运行。较早的 947c3067 使用独立安装的 rustc 验证了 140 个 ROS 1 报文向量。[公开候选的原生发行包](https://github.com/UlteSoft/uwvm2-ros-sdk-v2/tree/ba811556362cf721bda0a27b8469e6da73d436aa/bin/packages/linux-x86_64)
- **Ruby** (`ruby`). 已放入 mruby 4.0.0 运行时、原生 gem 和 Ruby 核心类的可编辑源码，仍待 MTE 编译及安装后的用户工程实测。[mruby 源码与提交](../../src/runtimes/mruby/upstream.json)
- **Swift** (`swift`). 待迁入 Swift 生产工具和目标运行时并净室验收。 `v1: install/catalog.json`
- **TinyGo** (`tinygo`). Unitree 的默认和显式二进制安装分别通过独立工程、Xmake 及 INT/AOT。TinyGo 0.38.0 使用专用前端、运行时和 32 位 Go 字长。它与标准 Go 共享语言计数，前端重建及厂商验收单独记录。 [Unitree](../qualification/unitree-b92c100d.json)
- **TypeScript** (`typescript`). ABB 位置示例在另行提供 Node.js 22.22.3 后通过 INT/AOT，该项宿主依赖在早期公开候选 `36c098e8` 中需要另行提供。候选 `947c3067` 已随包提供固定版本的 Node 可执行文件。
- **Visual Basic .NET** (`vbnet`). 旧版数值型 AOT 组件待迁入和复验。 `install/packages/vbnet/numeric.json`
- **WAT** (`wat`). 保留 WAT 汇编语言和独立的 `wrwat` 汇编器。历史冻结提交已验证源码重建、逐字节比对、Core Wasm、实际线程和 INT/AOT。Franka 从二进制和源码安装得到相同的汇编器，两种安装均在外部工程通过 Xmake 和双引擎。[Franka WAT](../qualification/franka-17ff81a1.json) `language/wat`
- **Zig** (`zig`). 已移入官方 0.16.0 完整源码和旧 SDK 的 LLVM IR 标记工具。原生安装、各目标配置及厂商客体运行待验收。[Zig 源码](../../src/compilers/zig/README.zh.md)

## 补充语言的源码依据

旧版 29 个选择项扣除互操作桥、合并两种 Go 工具链后，得到 26 种高级语言和 WAT。为推进超过 30 种独立语言的目标，从 300 包样本中选择了 Common Lisp、Ada、Tcl 和 Perl 作为补充候选。`cl_transforms_stamped` 含 Lisp 的 ROS 消息转换方法，Ada 样本提供 ROS 时间类型的生成绑定，VRPN 含 Tcl 应用脚本和用 Perl 写的宿主 RPC 生成器。四种语言的 SDK 编译器、来宾库和平台实测均待完成。[固定提交、用途及源码摘要](../../src/qualification/corpus/additional-language-inputs.json)
