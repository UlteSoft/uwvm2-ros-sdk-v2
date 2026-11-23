# 审阅候选验收记录

[English](../en/qualification.md)

以下结果分别对应指定的冻结提交。宿主为 Linux x86-64。净室使用空 HOME 和缓存、独立挂载 namespace 与嵌套 cgroup，父组和子组均限制 64 GiB、零 swap。运行 guest 和独立重建时切换到断网 namespace。开发检出不可见，宿主临时目录和共享内存目录不可写。

## 语言调试、dump 还原和热更新

本轮 C 和 C++ 验收覆盖五种 Linux 宿主 ABI 和十六档 guest 配置。每种语言都用安装所得的 SDK 编译器生成带调试信息的程序，再编译一个能观察到行为变化的版本。收据记录 SDK 提交、VM 提交及源码树、宿主可执行文件摘要、guest 摘要、配置和请求的引擎。

- 同时指定 INT 和 DBG 时，VM 必须明确报告该组合不受支持并退出。这一项按预期拒绝计数。LLVM AOT 承担源码断点、单步和变量检查的正向验收。
- 源码调试需要命中可执行的 C 或 C++ 源码行，检查变量值，再单步到另一行。
- dump 还原需要在协作停止点保存完整快照，让程序继续或改变可观测状态，随后恢复快照，核对恢复后的状态和继续执行的结果。
- 热更新需要在同一 VM 进程中通过生产签名更新通道提交新版本，记录提交前后调用同一导出函数的返回值及版本代数。

还原与签名更新分别使用各自的 VM 启动配置。每项能力均按 INT 和 LLVM AOT 记录实际通过、拒绝、不支持、失败和未测试的情况。公开安装、源码编译和 DWARF 检查也分别保留证据。[VM 快照契约](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/documents/runtime/unified-snapshot.md) · [VM 生产更新契约](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/documents/runtime/production-update.md)

## ABB 标准 Go 候选 a5863c63

公开源码安装器先用原始 Go 1.24.2 构建宿主启动器，再应用客体运行时修改。独立断网重建的 wrgo、asm、compile、link 四个 ELF 和四个 tar.xz 均与公开二进制安装逐字节相同。上一版 28466433 的 wrgo 字节差异已在这个提交修复并实测。两套安装各自直接编译并通过 Xmake 构建了 140 个 ROS 1 参考向量及 RAPID/EGM 应用。所得 Wasm 经 INT 和 AOT 实际运行。[逐包摘要和隔离配置](../qualification/abb-a5863c63.json)

## Unitree Python 候选 a524390d

默认 `py` 和显式二进制 `python` 分别安装了 CPython 3.14.8。两个安装所得的解释器均在 INT 和 LLVM AOT 中运行了外部 Python 工程，核对 WASI 平台、解释器版本、类、异常、容器、math 和 JSON。VM 记录了 `fd_tell` 拒绝，程序正常完成。另一次源码安装使用两个构建作业，在断网环境实际编译了 CPython。重建的目标静态库和共享解释器与二进制安装版均有字节差异。独立工程还验证了 43 种 Unitree 消息、172 次往返和四个 Fast-CDR 参考帧。按来宾文件路径启动脚本在默认 MTE 下以 120 退出，关闭运行时标签后，导入同目录模块仍在目录枚举时报错。TinyGo 的默认编译已通过 stderr 测试。调试编译在 EH 开启时无法汇编运行时 panic.S。[CPython 和 TinyGo 实测](../qualification/unitree-a524390d.json) · [安装和运行命令](languages/py.md)

## Franka 候选 17ff81a1

标准 Go 和 TinyGo 的默认与显式二进制安装各构建了 SDK 外的 Franka 工程。每个选项均验证了 8 种消息的 32 帧独立 Fast-CDR 双字节序参考数据，以及 4 个应用样本的双字节序往返。直接编译和 Xmake 的 Wasm 逐字节一致，在 INT 和 AOT 均通过。WAT 源码安装自行下载固定的 Rust 1.98.0 并在断网环境构建汇编器。所得 `wrwat` ELF 与二进制安装版逐字节相同。两种安装均汇编并运行了同一个外部 Franka 工程，随包解释器和 AOT 引擎均通过。额外探测的 `wrwat --version` 返回了不支持该选项。[Franka 证据](../qualification/franka-17ff81a1.json) · [Go 与 TinyGo 工程](../../include/u2rosv2/platform/franka/go/README.zh.md)

## GitHub 候选 28466433

ABB 在此提交上逐一尝试了 29 个旧选择。9 项完成安装，默认外部 Xmake 工程在两种引擎通过，20 项被安装器拒绝。QuickJS 的进程记录显示包内私有 C 编译器实际参与客体构建。标准 Go 和 TinyGo 分别匹配 163 个场景导入，INT 和 AOT 各执行了 163 次显式拒绝。两套工具链的二进制与源码安装均通过 140 个独立 genpy 报文向量，并检查了 5,113 个截断输入及 268 个非法布尔值或计数位点。

标准 Go 的源码安装逐字节重现了汇编器、编译器和链接器，启动器与下载版存在差异。先用原始宿主 Go 构建启动器，再应用客体运行时修改，就能重现公开 ELF 和归档。TinyGo 源码验收复用了已独立构建的 LLVM 19、23；启动器与 IR 准备工具重现了公开文件，完整宿主前端 ELF 仍有差异。WAT 显式使用官方 Rust 1.98.0 后，重现了汇编器 ELF 和归档。此提交的默认 WAT 源码安装在宿主缺少 Cargo 时失败。 [ABB](../qualification/abb-28466433.json) · [可复跑的独立 Go 工程与报文样本](../../src/qualification/abb/go)

## GitHub 候选 b92c100d

Unitree 逐一尝试了 29 个旧版选择项。C、C++、Rust、标准 Go、TinyGo、AssemblyScript、JavaScript、TypeScript 和 WAT的默认安装和外部 Xmake 工程通过，另有 20 个选择项被安装器拒绝。标准 Go 和 TinyGo 分别直接编译并用两种 VM 引擎运行独立报文工程。43 个上游类型涵盖 257 个字段，双端序的 Go2 和 HG 参考数据来自 Fast-CDR 2.2.5。标准 Go 的四个宿主程序从公开源码重建后与下载版一致。 [Unitree](../qualification/unitree-b92c100d.json)

## GitHub 候选 1259ec52

ABB 的 C、C++、Rust 分别默认安装了原生编译器。各自产生的 wasm32 和 wasm64 模块均匹配 163 项 VM 注册，两个引擎分别执行显式拒绝用例。三种语言的独立工程通过 140 个 genpy 参考报文。C++98/03/11/14/17/20/23/26 的工程分别通过。 [ABB](../qualification/abb-1259ec52.json)

公开 ABB Rust 源码安装耗时 27 分 16 秒，在联网 namespace 编译且 Cargo 使用离线模式。随后仅用该安装前缀在新断网 namespace 通过 32 项工程与 ABI 检查。另一次重建从头至尾断网，两个安装选中的 64,402 个 Rust 源文件具有相同路径、权限、大小和摘要。两次重建得到的编译器、驱动库以及两份重打的归档都与 GitHub 下载版逐字节一致。 [Rust](../qualification/abb-1259ec52.json)

Franka 的 WAT、C、C++、Rust、AssemblyScript、JavaScript 和 TypeScript 均从 GitHub 默认安装了编译器、Xmake 与 VM。随包工程和独立 Elbow 工程分别通过直接编译、Xmake、INT 和 AOT。C、C++ 和 Rust 另运行了类型化 XCDRv1 工程。C11/17/23 与 C++98 至 C++26 的八种标准通过，wrc 拒绝 C99。其余 22 个旧选择中，Go 和 TinyGo 缺 Franka 绑定，20 项缺语言入口。WAT 的源码安装两次在获取不同 Git 对象时失败。 [Franka](../qualification/franka-1259ec52.json)

## GitHub 候选 947c3067

ABB 的 C、C++、AssemblyScript、JavaScript、TypeScript 和 WAT 均在独立项目通过直接编译、Xmake 和双引擎运行。C、C++、Rust 的独立原始导入各有 163 条，另用 140 个 genpy 序列化样本逐字节验证了 ROS 1 报文。Rust bindings 模式依赖另行提供的 Rust 1.98.0 及 wasm32 目标库。公开候选的原生 Rust 源码安装在提供官方 stage0 后仍缺上游文件。独立诊断副本恢复这些文件后生成的 wrrs 实跑了 wasm32 和 wasm64；它的结果单独列出。[ABB 运行、权限和重建明细](../qualification/abb-947c3067.json)

Unitree 的 29 个旧版选择项逐一从空环境安装。C、C++、Go、WAT、JavaScript、TypeScript 和 AssemblyScript 的已安装工程通过 Xmake 与 INT/AOT。标准 Go 的默认安装、显式二进制安装和源码安装均在独立工程通过直接编译与 Xmake，四个原生工具逐字节相同。独立工程核对 43 种消息的 257 个字段，并用 Fast-CDR 2.2.5 的双端序样本验证 Go2 和 HG 的完整 LowState。TinyGo 默认安装缺少已登记的 wrtg 发行包，源码安装在 LLVM 配置阶段缺少 libc。[逐项结果、配置开关及产物摘要](../qualification/unitree-947c3067.json)

Franka 的 C、C++、WAT、JavaScript、TypeScript 和 AssemblyScript 共 8 个随包工程从 GitHub 安装后通过直接编译、Xmake 和 INT/AOT；另行提供 Rust 1.98.0 的 wasm32 工具链后，bindings 模式的两个 Rust 工程也通过。七种语言各自在来宾中解析两份独立的 Elbow 报文。另用安装头在宿主机验证全部 137 个 XCDRv1 记录，逐一比对 Fast-CDR 2.2.5 与 ROS 2 Jazzy rosidl，覆盖 818 个参考报文和每个配置 47,612 个截断位置。该提交尚缺 Franka 的 Go 和 TinyGo 绑定。[各工程运行结果](../qualification/franka-947c3067.json) · [逐字节参考数据](../../src/qualification/franka/xcdr1-vectors.json)

## ABB ROS 1 候选

独立测试从 GitHub 根安装器按提交 `36c098e85098d7ccc26562972af32f47aafe7560` 安装。旧版 29 个选择 ID 各自使用空 HOME 和空缓存。C、C++、JavaScript、WAT 使用安装所得 SDK 在断网外部工程构建，产物都通过解释器和 LLVM AOT。JavaScript 和 WAT 运行的是 ABB 位置只读接口。AssemblyScript 与 TypeScript 额外提供 Node.js 22.22.3 后跑通。Rust 需要仅安装绑定的参数，以及另行提供的 Rust 1.98.0 编译器和 wasm32 目标库。其余 22 项均被安装器拒绝，其中标准 Go、TinyGo 和 C 互操作桥分别实测。[各选项与 Wasm 结果](../qualification/abb-36c098e8.json)

C 和 C++ 的服务及系统状态示例均通过直接编译与 Xmake，C++98 至 C++26 的八种标准逐一通过。C、C++、Rust 各自核对了 70 个报文主体的 140 个独立 genpy 序列化用例、47 个 ABB 握手 MD5 和 `std_msgs/Header` 的 MD5。测试范围是 guest 内存中的 ROS 1 报文，驱动传输、RobotStudio 和控制器运行仍待验。[固定字节样本与上游提交](../../src/qualification/abb/ros1-vectors.json) · [ABB 示例及支持类型](../../platform/abb/ros1.zh.md)

## Franka 候选

在同一 GitHub 提交上，C、C++、WAT、JavaScript 均从独立工程离线构建 Franka 示例并通过 INT/AOT。独立 guest 使用 eProsima Fast-CDR 2.2.5 产生的 84 字节大端、小端 XCDRv1 报文验证了 Elbow 的两个公开读取接口。30 份上游 ROS 2 定义逐字节匹配。该提交仍缺 Elbow 的其余三个字段及另外 29 份定义的公开类型化 API，Franka 定义读取器在第 43 行报语法错误。AssemblyScript 和 TypeScript 缺指定 Node.js，Rust 缺自带编译器及 wasm32 目标库。安装逐项实测了 29 个 ID。[各语言结果、字节样本和上游提交](../qualification/franka-36c098e8.json)

## 安装所得 SDK

提交 `24e4cb6be1748d11a743393abd4cc9fce53b9eaa` 经 GitHub 根安装器取得。C、C++、WAT 在 generic 和 Unitree 均成功安装，六份清单和原生归档均经校验。8 个随包 Xmake 工程在安装目录外构建并通过 INT/AOT，其中包括 zlib Adler-32 组件和 ROS angles 组件。Unitree 使用已记录的 Go2 状态数据。

安装所得 wrc 和 wrcc 各生成了含 163 个已注册 ROS 导入的 Wasm，两个引擎分别逐个执行显式拒绝路径。小型 guest 验证了按需导入。默认 wasm32、Core 3.0、EH、单线程下，C 和 C++ 的实际产物均包含 WasmMTE 指令。C++ 分别验证了标准 Wasm EH 和 Herbceptions 类型化捕获，C 驱动拒绝 Herbceptions 选项。

该提交直接调用编译器时，Unitree 平台头仍需要手填搜索路径。直接编译和 Xmake 均缺 wasm64、threads、关闭 EH 和关闭 MTE 所需的 C/C++ 预编译目标。C 选择还携带共用 sysroot 中的 C++ 库。后续提交对这些项目分别重新验收。

提交 `d8e730f70ef12a31eb007ff8165073d95bf7bf36` 在两个平台上分别经源码与二进制安装得到相同的 wrwat ELF，独立断网重建逐字节一致。线程用例真实创建了 WASI 线程，并跨线程传递带标签的指针。该提交的原样 Xmake 工程曾解析失败，修正版已在上述六份安装中复验。[WAT 证据](../qualification/wrwat.json)

## 各语言独立绑定

C11、C++17 和 Rust 分别从独立用户工程编译。三者的全量 Wasm 均匹配 163 个函数名、命名空间和签名，仅调用 ABI 的工程各有 1 项导入。30 项 INT/AOT 测试覆盖授权、显式拒绝、隐藏导入和 guard 资源生命周期。Rust 此项使用 rustc 1.98.0 和官方 wasm32 标准库。带 MTE 的可安装 wrrs 待交付。[绑定证据](../qualification/bindings.json)

## 其余覆盖

- v1 清单有 29 个语言条目，含 C FFI bridge，有 36 个平台条目，含 ROS、ROS1、ROS2 和 WASI。旧 v2 工作清单有相同的 29 个语言 ID 和 32 个厂商或平台 ID。
- 标准 Go 的 Unitree 安装已通过。当前编译器拒绝 wasm64、共享内存线程以及 32 位 Go 指针配置。TinyGo、Fortran、Java、Kotlin、C#、其他待移植的原生及 AOT 工具链和解释器仍需各自取得发行验收。其余厂商与语言组合须在实际安装后的外部工程运行。
- 从 9,432 个库存包名中可复现地选择了 300 个移植样本。实际编译过的 angles 组件属于该队列，整包验收仍待完成。非 ROS 的 zlib 校验和组件单独计数。[样本源码清单](../../src/qualification/corpus/selection.json)
- 新版仍需完成全配置资格、多 Wasm 工程、近邻标签、远距离碰撞、协程和性能测量。部署和真机验收在 SDK 验收之后进行。

## 从源码构建的 wasm64 C/C++ 库

wasm64 生产构建使用提交 `7f6f3a1599c7722df5d56bdaf28eea46a1002cde`。使用 `374b5235d70ba0bce403d589f0678274a30eaf3a` 的驱动链接后，C 和 C++ 产物均具有 8 字节指针、64 位线性内存和 WasmMTE 指令。C 程序执行了 64 位 WASIp1 时钟调用、堆分配和格式化输出。C++ 程序执行了浮点 `to_chars`、动态字符串和跨栈帧异常展开。两种语言的 INT 和 AOT 共四项均返回预期退出码。本次使用已发行的原生工具和本地重建的目标库。[逐项结果和源码摘要](../qualification/wasm64.json)

## AssemblyScript 分域基础接口

冻结提交 `b9fee6fe06f4876a0ca4bb473a966fe770559158` 使用固定的 asc 0.28.20 编译。WABT 独立读取最终 Wasm，163 项导入的模块名、函数名、形参和返回类型全都与 VM 契约相符。38 个域分别编译，统一入口也可编译，只调用 guard.trigger 的工程保留一个导入。INT 和 AOT 各验证了五个用例，包括授权、显式拒绝和隐藏入口。此项使用可编辑源码树中的 AssemblyScript 工具和外部 Node.js 22.22.3。该提交在缓冲区重叠和长度槽说明上存在已发现的问题。[逐模块摘要和运行记录](../qualification/assemblyscript.json)

## 平台示例及严格 C++ 标准

提交 `663aab60ba1acacac54d1a8c18ea8140bf84f2b4` 通过本地冻结 Git 对象和已经校验的发行物安装了 C、C++、WAT、实验性 Rust 的全部 37 个选择。148 个外部 Xmake 工程均构建成功，在两个 VM 引擎上通过了 296 次执行。另做严格标准检查时，35 个平台的头文件和示例在 C++98/03 因 64 位整数字面量失败。43 个通用 C++ 头分别通过八种标准的独立编译。扩展平台语言和目录迁移后的版本需要在新的冻结提交上重新验收。[逐工程模块摘要与结果](../qualification/platforms-663a.json)

## JavaScript 和 TypeScript 源码驱动

在冻结提交 `e9ce427de3bda374304b0bf5dfc90ced43bee861` 上，QuickJS 和 TypeScript 两个实际 Wasm 均由 WABT 独立核对了 163 项 ROS 导入及其完整签名。另有一项 WASIp1 时钟导入。INT/AOT 的 24 个用例全部符合预期，覆盖授权、拒绝、隐藏导入、bigint 精度和缓冲区。外部 Xmake 工程显式调用源码驱动，四项运行通过。同一提交自带的安装器和 Xmake 规则拒绝这两种语言，所选 sysroot 也缺少关闭 MTE 或开启严格内存资格检查所需的发布记录。迁移后的安装器和语言规则需要在新提交单独验收。[冻结结果与模块摘要](../qualification/ecmascript-e9ce.json)

已按 SHA-256 核对 300 个入选包的 255 份源码归档，并从每份归档读取完整 Git 提交号。它们只计入源码取材，整包编译和移植实测另行记录。[抽样清单](../../src/qualification/corpus/selection.json) · [归档摘要对应的 Git 提交](../../src/qualification/corpus/archive-commits.json)
