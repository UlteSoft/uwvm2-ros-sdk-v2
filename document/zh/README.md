# WROS SDK 开发指南

[使用 wrcc 编写类型化错误返回](cpp.md)

[Nim 应用开发](nim.md)

[移植 ROS 包内资源](migration.md)


[WasmMTE 的检测范围](memtag.md)
- [内存标签工具链的本地验收与签署](memory-qualification.md)

驱动、模型和部署权限的边界见[本机驱动与模型接入](local-attachments.md)。

[用 xmake 构建和运行 Wasm 项目](xmake.md) · [xmake API 索引](xmake-api-index.md)

## 编译器命令名

公开编译命令统一为 `wr` 加语言简写。安装和 Xmake 配置使用语言 ID，实际编译时从所选安装目录的 `bin` 中调用对应命令。

| 语言 | 安装 ID | 编译命令 |
| --- | --- | --- |
| C | `c` | `wrc` |
| C++ | `cpp` | `wrcc` |
| Objective-C | `objectc` | `wrobjc` |
| Fortran | `fortran` | `wrf` |
| Rust | `rs` | `wrrs` |
| TinyGo | `tinygo` | `wrtg` |
| Nim | `nim` | `wrnim` |
| Lua | `lua` | `wrlua` |
| [JavaScript](js.md) | `js` | `wrjs` |
| [D BetterC](d.md) | `d` | `wrd` |
| Java | `java` | `wrjava` |
| Kotlin | `kotlin` | `wrkt` |
| C# | `csharp` | `wrcs` |
| [Visual Basic](vbnet.md) | `vbnet` | `wrvb` |

Java 和 Kotlin 默认安装同步 AOT 开发包，可选择经授权的本地编译现场。C# 的默认安装支持编译独立整数方法。完整 CLR 开发包仍待验收。 [C# 编译指南](csharp.md)可用 `revision-help` 查询指定提交的命令名，再用 `plan` 核实该提交实际提供的组件。静态归档工具使用 `wrar`。已固定到旧提交的安装继续使用对应提交的命令。

## 按 commit 安装

使用 Python 3.11 或更高版本。REV 必须是可信的 40 位小写 Git commit。固定入口可用于后来遵循同一安装协议的版本。用普通开发用户执行脚本。


新机器上只需获取首次提交的安装入口文件。将 `REV` 设为要安装的完整提交 ID。这个脚本可独立运行。

```sh
curl --fail --silent --show-error --output bootstrap.py \
  https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/cf09b4b30e3801deb73c012957b9f1c5f1196289/install/bootstrap.py
printf '%s  %s\n' e93d8e7c2fe733d8c33ca09c5dfee38d5047b0c11ba0524b5b2d8fecb36f1f29 bootstrap.py | sha256sum --check -
python3 bootstrap.py revision-help --commit "$REV" --language cpp --platform unitree
```

```sh
python3 install/bootstrap.py plan --commit "$REV" --language cpp --platform unitree
python3 install/bootstrap.py install --commit "$REV" --language cpp --platform unitree --prefix "$SDK_HOME"
python3 install/bootstrap.py revision-help --commit "$REV" --language cpp --platform unitree
```

固定命令为 `plan`、`install` 和 `revision-help`。后续版本的参数放在 `--` 后面。指定 `--local-repository` 可以离线读取本地 Git 对象。引导器先读取所选 commit 的 Python 脚本和必要的小清单，再逐文件校验大小和 SHA-256。所有成员校验通过才发布安装目录。相同摘要的文件可以复用，输出的 requested_paths 可用于核对传输范围。版本脚本是所选提交中的可执行代码。

`--component protocol` 安装通用协议及指定平台的来源记录。`--component compiler-source` 在安装选定语言的同时取得共享 Wasm LLVM 后端及 sysroot 的固定源码和补丁。C、C++、Fortran、Lua、Objective-C、Rust 和 TinyGo 均可选择这个组件，各语言前端、标准库及运行时依赖见对应语言指南。常规开发安装只取对应开发文件。

已有编译环境时，可使用 `-- --component bindings` 单独安装所选语言的原始声明、许可证以及所选语言和平台的元数据。C 和 C++ 共用头文件，本修订还提供 Rust 和 AssemblyScript 的声明。此模式仅请求这些文件。首个 commit 的安装入口也可通过 `revision-help` 发现新选项。


D 可选择 `--language d -- --component bindings`。安装内容包括 `language/d/wros_scene.d`、对应的 C 导入适配代码和 ROSv2 头文件。D 模块可用 `import wros_scene : wros_abi;` 导入并调用 `wros_abi()`。i32 和 i64 操作数分别使用 D 的 uint 和 ulong。这个组件提供通用层全部 163 个操作的原始声明。[BetterC 验收程序](../../tests/d_bindings/qualify.py)用 wasm32 应用测试 VM 授权和拒绝 ABI 查询。[D 开发包](d.md)提供经站点签署的 BetterC 编译器和 Xmake 适配，已验证 wasm32 单线程。完整 DRuntime 和垃圾回收仍待验收。

### 从公开安装编译第一个 Nim Wasm 应用

这个示例固定到已通过空缓存安装测试的 SDK 提交。请使用部署方签发的 Nim 站点配置，其中指定了已审核的宿主编译器、目标 sysroot 和与 VM 对应的发行资格。需要 Python 3.11 或更新版本。

```sh
REV=f8349b2666c8dd97957e94afe50c547f232a5249
curl --fail --silent --show-error "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$REV/install/bootstrap.py" | python3 -I -B - install --commit "$REV" --platform unitree --language nim --site-profile /etc/wros/nim-site.json
SDK="$HOME/.local/share/wros-sdk/$REV/unitree/nim/development"
"$SDK/bin/wrnim" "$SDK/examples/nim/body.nim" --build-receipt -o robot.wasm
```

这个选择在空缓存中只拉取了 53 个文件。实测也用安装目录里的 Xmake 适配器生成了应用，并在两个 VM 引擎运行。示例查询 ROS ABI，宿主需要向该模块开放 `uwvm_ros_v2.abi`。运行前可使用该 VM 核对构建收据。[Nim 编译器与支持的配置](nim.md) · [Xmake 构建配置](xmake.md)


### 一条命令安装宇树开发工具

在 Bash 中将 `REV` 设为可信的 40 位 SDK 提交 ID。以下命令直接从官方仓库下载安装入口和所选文件。

```sh
set -o pipefail
curl --fail --silent --show-error \
  "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$REV/install/bootstrap.py" | \
  python3 -I -B - install --commit "$REV" --platform unitree --language fortran
```

安装结果的 `directory` 字段给出 SDK 目录，其中包含 C 前端 `bin/wrc`、C++ 前端 `bin/wrcc`、Fortran 前端 `bin/wrf` 和归档工具 `bin/wrar`。语言源码与 Xmake 平台文件分别选取 Fortran 和宇树对应的包。下载中断后，使用相同前缀重复执行即可复用已校验的对象。

构建时，`PRODUCER` 指向本机已审核的编译器目录，`RECEIPT` 指向对应的 sysroot 构建记录。前端会校验所选构建输入。默认内存标记配置还需要运营方针对这些输入和选项签署的资格记录。宿主工具链、sysroot 和 VM 需要单独准备。[宿主工具及本地资格验证](fortran.md)

```sh
sdk="$HOME/.local/share/wros-sdk/$REV/unitree/fortran/development"
"$sdk/bin/wrc" --toolchain "$PRODUCER" --sysroots "$RECEIPT" --target wasm32 -O3 -g body.c -o body.wasm
"$sdk/bin/wrf" --toolchain "$PRODUCER" --sysroots "$RECEIPT" --target wasm32 -O3 -g "$sdk/examples/fortran/body.f90" -o robot.wasm
```

### 使用站点预置的工具链安装 C、C++ 或 Fortran

若运营方已准备 LLVM 工具链、sysroot 和与所选 SDK 修订对应的签名资格声明，可在安装时指定其提供的站点配置。在 Bash 中将 `REV` 设置为可信的完整提交 ID 后，执行一条安装命令。

```sh
set -o pipefail
curl --fail --silent --show-error "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$REV/install/bootstrap.py" | python3 -I -B - install --commit "$REV" --platform unitree --language c --site-profile /etc/wros/c-site.json
```

使用安装后的编译器构建 C 程序。资格记录决定默认地址宽度、线程、异常模式、优化级别与调试符号。

```sh
"$HOME/.local/share/wros-sdk/$REV/unitree/c/development/bin/wrc" main.c -o app.wasm
```

Fortran 的站点工具链还需提供经审核的 WebAssembly Flang 和匹配的 MTE 工具。签名声明须包含 Fortran 及其桥接层与运行库使用的 C、C++ 资格记录，三者对应相同的目标配置、构建选项和 VM。以下命令仅选择宇树平台的 Fortran 开发包。

```sh
curl --fail --silent --show-error "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$REV/install/bootstrap.py" | python3 -I -B - install --commit "$REV" --platform unitree --language fortran --site-profile /etc/wros/fortran-site.json
```

使用站点签署的默认选项编译已安装的示例。

```sh
sdk="$HOME/.local/share/wros-sdk/$REV/unitree/fortran/development"
"$sdk/bin/wrf" "$sdk/examples/fortran/body.f90" -o robot.wasm
```

运营方提供的本地 JSON 包含下列字段。示例路径与摘要占位符需替换为经过审核的值。

```json
{
  "toolchain": "/opt/wros/llvm",
  "sysroots": ["/opt/wros/wasm32-eh/sysroots.json"],
  "trust": {
    "verifier": "/opt/wros/bin/cosign",
    "verifier_sha256": "<已审核的验证程序 SHA-256>",
    "policy": "/etc/wros/release.policy",
    "statement": "/etc/wros/release.wasm",
    "statement_sha256": "<已审核的签名声明 SHA-256>"
  }
}
```

签名声明应包含一条适用于所选语言的资格记录。如有多条，增加 `release_sha256` 字段，指定资格工具生成的记录规范化摘要。安装时核验签名、编译器、sysroot 文件及所选 SDK，并输出 `site_release_sha256`。每次严格构建都会重新校验实际输入与签名资格。宿主工具和资格声明继续使用运营方管理的路径。以同一配置重复安装会重新校验，切换配置可使用新前缀。C++ 使用 `--language cpp`、`bin/wrcc` 和 C++ 对应的资格记录。

### 修订脚本和文件清单格式

固定入口为所选提交中的 `install/revision.py`。安装器通过 Python 隔离模式执行该脚本，依次传入平台名、语言名以及分隔符 `--` 后的扩展参数。`revision-help` 传入 `--revision-help`，读取含 `help` 字符串的 JSON 对象。正常选择时，脚本向标准输出写入一个 JSON 对象，例如

```json
{"variant":"bindings","packages":["platforms/unitree","metadata/cpp","license","bindings/c"]}
```

每个包名对应同一提交下的 `install/packages/<包名>.json`。清单的 `files` 数组逐项声明仓内相对路径、字节数 `bytes`、小写 SHA-256 和十进制 POSIX 权限 `mode`（420 或 493）。多个包引用同一路径时，元数据必须一致。单次选择最多 64 个包、8,192 个不同文件，单个文件上限 128 MiB，载荷总上限 1 GiB。安装目录为 `<prefix>/<commit>/<平台>/<语言>/<variant>`，同时通过结果字段 `directory` 返回。后续修订应保持首版基础命令和上述脚本格式。仓库中的 `tests/install_protocol_matrix.py` 从指定提交的 Git 对象执行安装，逐个核对所有已登记语言与平台组合的实际文件集合。

## 编译程序

`wrc` 用于 C，`wrcc` 用于 C++。PRODUCER 指向支持 WasmMTE 的专用编译器目录，RECEIPT 指向与这个编译器摘要匹配的 sysroot 构建记录。编译器和基础库的源码构建入口位于 `tools/wasm/memtag`。

```sh
bin/wrcc --toolchain "$PRODUCER" --sysroots "$RECEIPT" --reactor --export _start -O3 -g -o body.wasm body.cpp
```

默认 wasm32、Core 3.0、MTE、标准 Wasm EH，线程默认关闭。使用 `--no-mte`、`-pthread`、`--target wasm64`、`--no-eh`、`--core mvp` 选择对应配置。依赖 pthread 的构建须传递线程选项。地址宽度、线程、MTE 和异常模式各自决定可使用的 sysroot。链接后检查实际导入名和签名，拒绝通用 POSIX 套接字。允许 WASIp1 环境变量查询、时钟读取、时钟分辨率查询和进程退出。运行权限另由 VM 控制。

### 分文件编译与静态库

用 `-c` 编译一个翻译单元，以 `wrar` 建立静态库，再链接目标文件和库。各步骤必须选择相同编译器与 guest 配置；C 和 C++ 可以使用同一配置。`-I` / `--include-dir` 指定头文件目录，`-D` / `--define` 定义对象式宏，`--std` 指定语言标准。前端只提供已说明的 Wasm 选项，不转发任意 native 编译或链接参数。

```sh
bin/wrcc --toolchain "$PRODUCER" --sysroots "$RECEIPT" -O3 -g \
  --std c++20 -I include -DROBOT_AXES=6 -c control.cpp -o control.o
bin/wrar --toolchain "$PRODUCER" -o libcontrol.a control.o
bin/wrcc --toolchain "$PRODUCER" --sysroots "$RECEIPT" -O3 -g \
  --reactor --export _start main.cpp libcontrol.a -o robot.wasm
```

`wrar` 调用指定工具链的 `llvm-ar`，产生可复现、带符号索引的普通 GNU 静态库，不执行 guest，也不安装 native 库。目标文件中的 `wros.sdk.object` 自定义段记录文件摘要、编译器摘要、位宽、Core、MTE、线程和 EH 配置。配置混合、文件变化、无记录目标文件、ELF、LLVM bitcode 和 thin archive 均拒绝。这个记录仅检查构建一致性，不是签名；有权修改构建输入的人也能制造记录。应使用受信编译器和已签名部署文件，运行安全边界仍由 VM 实施。

链接前检查库中所有成员，包括未引用成员；复制已验证的目标字节到私有目录，重建符号索引后再链接。最多接收 1,024 个目标成员，单个目标文件或库上限 128 MiB，合计上限 256 MiB，最终文件上限 128 MiB。失败保留原输出。最终 Wasm 删除构建记录后仍独立检查实际导入，配置匹配不代表允许文件或套接字能力。

时钟接口为 `clock_time_get` 和 `clock_res_get`。wasm64 使用同名的 `_wasm64` 形式。两种宽度的时钟 ID 都是 i32，精度参数都是 i64，结果缓冲区地址随目标宽度变化。部署时可以分别授予单调时钟或实时时钟的读数与分辨率查询权限。

wasm64 环境变量接口采用对应 UWVM sysroot 的 `environ_get_wasm64`、`environ_sizes_get_wasm64`（i64 指针）和 `proc_exit_wasm64`。这是 UWVM 对 Preview1 的扩展，不是标准 Preview1 memory64 ABI，不能混用 wasm32 名称。缺少 memory64 线程启动支持时明确拒绝。

sysroot 使用上游 libc++abi 的 bare-metal 配置、静默 terminate，以及摘要锁定的内部诊断补丁。补丁保留断言检查和致命错误的 Wasm trap，移除内部 stderr 输出及由环境变量开启的 unwinder 追踪，开启断言的构建也遵循这一规则。异常传播仍保留，不关闭应用自身日志，也不授予外部操作权限。应用诊断应走已授权的 ROSv2 操作。基础库保留优化和完整调试信息，前端编译前检查所选头文件及库的摘要。

`tests/separate_compilation.py` 实际构建 wasm32/wasm64 目标与静态库，在 VM 两个执行引擎中验证跨文件异常、配置混合拒绝、环境变量权限。须经 VM 仓库 cgroup 入口运行。单项测试通过不等于全部标准库、ROS 包或厂商硬件完成验收。

C/C++ 使用 `<wros/scene.h>`。Rust 和 AssemblyScript 的底层声明位于 `language/`，对应本次 VM 登记的 163 项操作。旧清单共有 29 个标识，其中包含 WAT 和 C FFI 桥；平台登记为 32 个范围。默认开发包覆盖 C、C++、受限 D、数值 Fortran、JavaScript、Lua、Nim、Objective-C、Rust no_std、TinyGo 和独立标量 C#。Java 和 Kotlin 的默认开发包提供同步 AOT 编译器。各配置可用的标准库、MTE 验证范围、位宽、线程和异常选项各有差异。移植到某个平台的通用算法与厂商驱动、现场中间件需要分别验收。

C# 支持文档所述的标量计算及一条有类型的 ROSv2 ABI 查询。使用托管对象的应用仍需集成 CLR 和垃圾回收器。Jazzy tf2 的 C++ 移植组件可以生成严格单执行器的 BufferCore 覆盖头，线程构建仍需单独验证对应的 sysroot。下面的指南列出依赖、命令和已测试的程序范围。[C#](csharp.md) · [Java 与 Kotlin](jvm.md) · [Jazzy tf2](tf2-buffer-port.md)

## 厂商接入

SDK 的登记范围可扩展到国内和国际厂商。纯算法留在 Wasm，设备访问交给加密连接的隔离驱动。只有通用权限难以表达、且需要宿主执行的约束才进入 VM 平台扩展。上层拉取器按授权从厂商入口获取原厂文件，部署器只读取本地文件并验证摘要。协议来源、物理仿真和实体设备验收分别登记。

工业构建把每个目标文件与编译器摘要、目标配置（含 MTE 开关）及所选 sysroot 清单的摘要绑定。旧目标文件须重新编译再链接。构建会校验 compiler-rt、所选头文件和库；前提是编译器、sysroot 记录和构建输入可信。编译器省略栈标签的依据是静态分析能够证明相关访问的边界和生命周期。回归通过只能验证已测路径，不能据此断言整个程序内存安全。

发布的每个语言编译器都必须支持 WasmMTE，默认启用。可用 `--no-mte` 关闭整个目标的插桩，并使用对应的 sysroot。C/C++ 可以通过 `no_sanitize("memtag")` 等源码属性局部改变插桩。源码作者的显式选择和编译器经边界、生命周期分析后自动省略标签，是两种独立机制。

[TinyGo](tinygo.md) · [Fortran](fortran.md) · [Rust](rust.md) · [Objective-C](objectc.md)

### 支持的 Wasm 格式

SDK 构建和运行 WebAssembly **核心模块**，可按项目选择 Core 功能级别。SDK 拒绝 WASI Preview 2、Preview 3 目标、Component Model 二进制、组件类型元数据和组件 ABI 的导入与导出。单独编译的对象及静态库的每个成员都遵守同一规则。应用通过 ROSv2 核心模块接口访问宿主，使用 Preview 1 的时钟或环境变量仍需 VM 单独授权。选择 Core 3.0 只控制 Wasm 功能级别。

## 运行外置驱动仿真

在源码目录运行 `tests/mujoco_guest.py`，会从指定语言的控制器源码构建 Wasm，在真实 VM 上运行，并通过认证的 TLS 会话连接外置 MuJoCo 人形机器人接收端。需要提供 VM 测试源码、VM 可执行文件、配套的 OpenSSL 和含模型的官方 MuJoCo 发行包。每次选择新的输出目录。

```sh
python3 tests/mujoco_guest.py --language lua \
  --vm-source "$VM_SOURCE" --runtime "$VM" --openssl-root "$OPENSSL" \
  --mujoco "$MUJOCO" --toolchain "$TOOLCHAIN" \
  --sysroots32 "$SYSROOTS32" --sysroots64 "$SYSROOTS64" --output "$OUT"
```

C、C++、Fortran、Lua、Nim 和 Objective-C 可选择双位宽测试。Rust no_std 和 TinyGo 当前测试 wasm32。Rust 指定 `--rustroot`，TinyGo 指定 `--goroot` 和 `--tinygoroot`，Nim 指定 `--producer`。Objective-C 还需 `--objc-clang`、`--objc-runtime32` 和 `--objc-runtime64`。Fortran 可指定 `--flang`。解释器和 AOT 都会执行三种场景，分别验证 128 步与原生仿真的一致性、越限指令被拒和接收端崩溃后的状态。各次使用的二进制与输入摘要、授权、后端、执行结果和原生参考值均记录在 `results.json`。使用开发工具链时可显式传入 `--candidate-mte`，此时保留插装，单次仿真不产生签名工具链资格。

测试 Unitree Go2 时，将 `SDK` 设为已签署的 Unitree D 开发安装目录，`GO2_ASSETS` 设为 VM 模型配置指定的原厂资产目录。夹具逐个编译 wasm32 BetterC 控制器，并通过安装的 `wrd` 验证收据。解释器和 AOT 均通过 D 声明调用驱动，测试正常步进、越限指令和接收端崩溃。

```sh
python3 tests/mujoco_guest.py --language d --installed-sdk "$SDK" --address-bits 32 \
  --vm-source "$VM_SOURCE" --runtime "$VM" --openssl-root "$OPENSSL" --mujoco "$MUJOCO" \
  --vendor-model "$VM_SOURCE/test/0084.ros-runtime/mujoco_profiles/unitree-go2.json" \
  --vendor-assets "$GO2_ASSETS" --output "$OUT"
```

使用签名的 TinyGo 站点时，将 `SDK` 设为已安装的 Unitree TinyGo 开发目录，并将 `--language d` 改为 `--language tinygo`。测试通过安装的 `wrtg` 编译 Go 控制器，在运行每个场景前验证构建收据与 VM 是否匹配。

Java/Kotlin 可选同步 AOT 组件使用 `set_wros_jvm_main(class_name)` 指定入口。详见 [JVM 编译与 Xmake 参数](jvm.md)。

[JavaScript 解释器与 ROS 接口](js.md)

[将 TypeScript 应用编译为 Wasm](typescript.md)

[分平台示例与 VM 测试](platform-examples.md)
