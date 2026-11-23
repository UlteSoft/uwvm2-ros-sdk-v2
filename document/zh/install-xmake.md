# 安装 SDK 并构建 Wasm 程序

[English](../en/install-xmake.md)

安装器从固定的官方项目获取宿主工具。[宿主工具](host-tools.md)

构建主机需要 Python 3.11 或更高版本和 Git。原生编译器二进制面向 Linux x86-64。构建示例需要 Xmake，运行示例需要带解释器和 LLVM 引擎的 `uwvm2-ros`。VM 仓库列出了宿主依赖，构建命令为 `xmake build uwvm2-ros`。[Xmake 安装指南](https://xmake.io/guide/quick-start.html) · [VM 构建说明](https://github.com/UlteSoft/uwvm2-ros)

## 确认 Linux 宿主 ABI

固定下列提交，在一个新目录里执行。输出中的 `host` 是当前 Python 用户态对应的原生工具包，`host_selections` 列出该提交为此宿主登记的语言。

```sh
hostrev=084c206553f46cbe1f421e9c2f9ef5855f128c08
mkdir -p .tmp
export TMPDIR="$PWD/.tmp"
curl -fsSL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$hostrev/install.py" -o install.py
python3 -I -B install.py list --commit "$hostrev" --prefix "$PWD/sdk"
```

两套 Cortex-A15 QEMU 系统都报告 `armv7l` 和 `AT_HWCAP=4176086`。armel Python 的 ELF 标志为 `0x05000200`，安装器选中 `linux-arm`。armhf Python 的标志为 `0x05000400`，选中 `linux-armhf`。安装器还核对已知动态加载器，并按进程实际可用的 VFP、NEON 等指令特性检查包的要求。此提交在五个宿主通过 `list`，其中 x86_64 有可安装的语言记录。[五宿主实测](../qualification/linux-host-abi-084c2065.json) · [Arm ELF 规范](https://github.com/ARM-software/abi-aa/blob/main/aaelf32/aaelf32.rst)

## 在五种 Linux 宿主上构建 ABB WAT 示例

此候选在原生 x86_64、i686 和 QEMU System 的 AArch64、ARM 软浮点、ARM 硬浮点用户态完成了 GitHub 安装。复制示例到安装目录之外，断网后即可用随包工具构建并分别用解释器和 AOT 引擎测试。两套 32 位 ARM 测试均启用 Cortex-A15 的 VFPv3、D32 和 NEON。软浮点系统关闭 VFP 后，安装器会因 Xmake 的指令要求而拒绝安装。[五宿主验收与四个重建摘要](../qualification/abb-wat-five-hosts-c5053769.json)

```sh
mkdir -p abb-wat-check && cd abb-wat-check
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
rev=c5053769afe1f08d38dbd6ca835ef98abd1df11e
curl -fsSL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$rev/install.py" -o install.py
python3 -I -B install.py install --commit "$rev" --language wat --platform abb --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -I -B -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM
cp -R "$UWVM_ROS_SDK_ROOT/examples/abb/wat" my-project
cd my-project
xmake build
xmake test -j1
```

## 在自己的工程中运行

以下命令分别固定根安装器和 SDK 的提交。根安装器下载所选 SDK 提交的 `install/install.py`。输出的 JSON 给出完整 SDK 提交号和安装目录的绝对路径。

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp"
export TMP="$TMPDIR" TEMP="$TMPDIR" XMAKE_TMPDIR="$TMPDIR"
bootstrap=35160a793faaca9ea7de9d6820687288b5373a78
revision=36c098e85098d7ccc26562972af32f47aafe7560
curl -fsSL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$bootstrap/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform generic --language wat --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export WROS_VM="$(command -v uwvm2-ros)"
cp -R "$UWVM_ROS_SDK_ROOT/examples/wat" my-guest
cd my-guest
xmake build
xmake test -j1
xmake run
```

若 VM 位于其他目录，将 `WROS_VM` 设为该可执行文件的绝对路径。`xmake build` 把 Core Wasm 模块放在工程的 `build` 目录。两个测试分别启动 VM 解释器和 LLVM 引擎，运行 guest 自己定义的 `_start`，并传播 trap 与失败退出码。WAT 示例查询宿主 ABI 并校验带符号的单位转换。装好 SDK 后，上述工程构建和运行可离线完成。

## 选择提交、语言和平台

回到含有 `install.py` 和 `selection.json` 的目录，用 `python3 install.py list --commit "$revision"` 列出所选版本的安装选项。`--commit` 接受完整的 40 位小写 Git 提交号。需要固定启动器本身时，也将原始下载地址中的 `main` 改成同一提交号。`plan` 会先列出该选择将获取的仓库文件和原生程序的安装位置。

```sh
REV="$(python3 -c 'import json; print(json.load(open("selection.json"))["commit"])')"
python3 install.py plan --commit "$REV" --platform unitree --language cpp --prefix "$PWD/sdk"
python3 install.py install --commit "$REV" --platform unitree --language cpp --prefix "$PWD/sdk"
```

- `c` 安装原生 `bin/wrc`、C 头文件和16 档 WASIp1 sysroot。
- `cpp` 安装原生 `bin/wrcc`、独立的 C++ 头文件和16 档 WASIp1 sysroot。
- `wat` 安装支持 WasmMTE 的原生 Core Wasm 汇编器 `bin/wrwat`。
- `as` 安装 `bin/wras` 与固定版本的 AssemblyScript 编译器包。安装器一并提供官方 Linux x64 版 Node.js 22.22.3。在需要指定同一二进制的其他副本时设置 `WROS_NODE`。[AssemblyScript 工程](languages/as.md)
- `js` 安装 `bin/wrjs`、QuickJS 和编译应用所需的私有 wasm32 C 后端。[JavaScript 工程](languages/js.md)
- `typescript` 安装 `bin/wrts`、使用 ES2022 严格模式的 TypeScript 编译器与 QuickJS 后端。构建需要与 AssemblyScript 相同的 Node 宿主程序。[TypeScript 工程](languages/typescript.md)
- `py` 和 `python` 可在通用、Unitree 平台安装 CPython。共享解释器运行脚本，`wrpy.py` 打包外部工程。[Python 工程](languages/py.md)
- `rust --mode bindings --no-mte` 安装实验性的 `no_std` Rust crate 与示例。适配层调用上游 `rustc`，目标为 `wasm32-unknown-unknown`，使用 `panic=abort`，关闭 MTE 和 EH。预先执行 `rustup target add wasm32-unknown-unknown` 安装目标，可用 `WROS_RUSTC` 指向指定的本机编译器。[Rust 官方目标文档](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html)

`generic` 安装通用场景 ABI。`unitree` 额外提供 Go2 低层状态只读契约与 `examples/unitree/<language>`。示例在 guest 内存中解码一份录制的驱动返回值。采集实时遥测需要部署方提供匹配的驱动及能力授权。安装后的平台手册位于 `platform/<platform>/README.zh.md`。[固定版本的 Unitree 提供方契约](https://github.com/UlteSoft/wasmros-deployer/blob/69e5e1be8fe3d669af962e5f63c147959ec45ad7/tests/support/unitree_low_state_contract.txt)

公开接口的根目录为 `include/u2rosv2/universal/<language>` 和 `include/u2rosv2/platform/<platform>/<language>`。语言目录名分别为 `c`、`c++`、`rust`、`wat`、`as`、`js` 和 `typescript`。二进制模式获取所选公共绑定、示例、运行依赖和所需的共享解码器。ECMAScript 使用的私有 C 后端和 TypeScript 使用的 JavaScript 实现位于 `libexec`。源码模式额外获取 AssemblyScript 或 TypeScript 的上游开发目录。

使用 `install.py list` 中的其他平台 ID，即可安装对应的只读 guest 解码库和 `examples/<platform>/<language>` 用户工程。例如，`--platform agilex` 读取 Scout 电池管理消息，`--platform fourier` 读取 Aurora 仿真器的 LCM 反馈。各平台手册标明输入范围、编码方式、已提供的字段及固定版本的上游定义。示例在离线环境中使用按定义构造的数据。

安装器校验 Git 对象以确认每个文件来自所选提交，并按长度和 SHA-256 核验 LFS 内容。每个原生程序采用单成员 USTAR `.tar.xz`，压缩包和解压后的 ELF 各有独立摘要。解包会核对成员名、权限、长度和 ELF 架构。所有所选文件完成后才发布到 `<prefix>/<commit>/<platform>/<language>/<mode>`。重复安装会检查现有文件。安装目录中的 `selection.json` 保留路径、长度、权限和 SHA-256。

## 从源码重建编译器

C、C++ 和 WAT 的 `--mode source` 获取所选编译器的可编辑源码，并构建其可执行程序。脚本语言的两种安装模式均使用固定版本的编译器或解释器，源码安装额外提供开发源码和验证材料。Linux x86-64 上的 WAT 源码安装默认从所选 SDK 提交下载 Rust 1.98.0 官方编译器、Cargo、宿主标准库及锁定的 Cargo 工程。构建前按照 `src/compilers/wrwat/bootstrap.json` 逐一核验压缩包及所选成员的摘要。安装器记录本地生成的可执行文件摘要。

```sh
python3 install.py install --commit "$REV" --platform franka --language wat --mode source --prefix "$PWD/sdk"
```

首次下载需要 Python 3.11 或更高版本、Git、可访问 GitHub 的 HTTPS 连接和可信 CA 证书。下载完成后即可断网构建。宿主需要 GNU/Linux x86-64、位于 `/usr/bin:/bin` 的可用 `cc` 链接驱动、glibc 的开发库及启动文件、libgcc、zlib 和 GNU `/usr/bin/strip`。Rust 编译器及配套 LLVM 库、GNU 风格 LLD 和 Cargo 均随选定压缩包提供。日后离线重建时，使用新输出路径执行 `python3 -I -B "$UWVM_ROS_SDK_ROOT/src/compilers/wrwat/rebuild.py" --output "$PWD/wrwat"`。已有匹配的官方工具链时，可以在安装或重建时指定 `--rust-bin /path/to/rust/bin`。使用该参数安装时将跳过三个引导包。[Rust 1.98.0 官方宿主发行清单](https://static.rust-lang.org/dist/2026-08-20/channel-rust-1.98.0.toml)

C/C++ 源码构建需要 CMake 3.26 或更高版本、Ninja，以及包含 `bin/clang`、`bin/clang++`、`bin/ld.lld` 的宿主 LLVM。安装器从仓内源码构建一次原生编译器、链接器和归档工具，再分别构建 16 档 WASIp1 sysroot。`--jobs` 控制 C/C++ 重建的并行度。

```sh
python3 install.py install --commit "$REV" --platform generic --language cpp --mode source \
    --bootstrap /path/to/host-llvm --jobs 4 --prefix "$PWD/sdk"
```

发布维护者可在源码仓库中只重建一个 guest 目标。工具链前缀需要 `bin/{clang,clang++,wasm-ld,llvm-ar,llvm-ranlib,llvm-nm,llvm-config}` 和 `lib/clang/23/include`。脚本在编译前校验已发布的 Clang、LLD、归档器及资源头文件的摘要，目标构建清单还会记录源码摘要、辅助工具摘要和所选 ABI。

```sh
python3 -I -B src/compilers/cc/rebuild.py --toolchain /path/to/producer \
    --target wasm64 --core 3.0 --eh --mte --no-threads --language cpp \
    --work "$PWD/.tmp/target-build" --prefix "$PWD/.tmp/target-release" --jobs 4
```

发布 wasm64 二进制包时，将生成的 `include/sysroot/c/`、`include/sysroot/c++/` 中的文件合并到仓库同名目录。每份共用头文件都须与使用它的各档构建收据一致。复制 `lib/wasm64-wasip1/<flavor>/` 的链接文件，以及 `share/toolchains/portable/sysroots/wasm64-wasip1/<flavor>/` 中的 `sysroots.json` 和 `clang-resource-headers.tar.xz`。将生成的库条目同步到本机和交叉构建宿主的发布清单。

## 配置 Xmake 目标

工程引入已安装的 `tools/xmake/ros.lua`，声明 `binary` 目标、语言和源文件，提供 guest 自己定义的 `_start`。C/C++ 目标可以包含多个翻译单元，支持 `add_includedirs`、`add_defines` 和 `add_wros_exports`。Rust 输入一个 crate 根文件。WAT 输入一个文本模块，并用 `add_wros_operations` 声明其 ROS 导入。`set_wros_test_queries("abi")` 在本地测试中授予只读 ABI 查询，省略它时测试 VM 保持默认权限。

C 系列 SDK 将 WASIp1 头文件安装在 `include/sysroot/c/`，将 libc++ 与 Herbceptions 头文件安装在 `include/sysroot/c++/`。Objective-C 系列另有 `include/sysroot/objc/` 下的 GNUstep 头文件。例如，`<stdio.h>` 对应 `include/sysroot/c/stdio.h`，`<vector>` 对应 `include/sysroot/c++/vector`。

安装器按所选配置的构建收据核验每份头文件，再将其硬链接到 Clang 自动搜索的多架构 sysroot。安装器根据 MTE 设置从 `c/config/mte/` 或 `c/config/nomte/` 选择 `wasi/version.h`，根据线程模型从 `c++/config/threads/` 或 `c++/config/single/` 选择 libc++ 的 `__config_site`。启用 EH 的配置同时提供 libunwind 头文件。静态库和启动对象位于 `lib/<triple>/<flavor>/`，构建收据与 Clang 内建资源头文件归档位于 `share/toolchains/portable/sysroots/<triple>/<flavor>/`。

C 系列目标可用 `add_links("wasi-emulated-mman")` 从所选 sysroot 链接可选静态库。直接使用编译器构建同一工程时可传 `-lwasi-emulated-mman`。

AssemblyScript 输入一个应用源文件。标量程序可用 `add_wros_operations("abi")` 声明 ABI 查询。使用有界暂存区时，设置 `set_wros_profile({as_driver = true})`。JavaScript 和 TypeScript 可用 `set_wros_entry` 在已声明的多个文件中指定入口，由后端导出 guest 的 `_start`。用 `add_wros_operations` 声明 ROS 导入，用 `set_wros_test_queries("realtime-clock")` 在本地 VM 中为 QuickJS 提供实时时钟。通用 ABI 示例同时声明 `"abi"` 和 `"realtime-clock"`。

```lua
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("controller")
    set_kind("binary")
    set_language("cpp")
    set_ros_platform("generic")
    set_wros_profile({abi = "wasm32", core = "3.0", memory64 = true,
                      mte = true, eh = true, threads = false, std = "c++20"})
    add_files("controller.cpp")
    set_wros_test_queries("abi")
    add_wros_tests("int", "aot")
target_end()
```

原生目标默认采用 Core 3、wasm32 语言 ABI，VM 启用 memory64，MTE 同步检查，开启 EH，关闭线程。C++ 额外默认启用 Herbceptions。`abi` 指定语言指针宽度，`memory64` 指定 VM 特性。WAT 在模块中显式声明内存类型，汇编时用 memory64 选项决定可接受的语法。`wrc` 和 `wrcc` 使用 `--target wasm32`（默认）或 `--target wasm64` 选择 sysroot。两者均在 `lib/<triple>/core3.0-eh-mte` 中提供 Core 3、静态链接、单线程、EH 和 MTE 配置的库。其他配置需要匹配的构建输入。

wasm32 目标在 VM 开启或关闭 memory64 时都使用 32 位 C/C++ 指针及 32 位主线性内存。wasm64 目标使用 64 位指针、`size_t` 和主线性内存地址，当前 LLVM 后端要求允许 `--memory64`，会拒绝 `--target wasm64 --no-memory64`。此目标使用 UWVM 的 Preview 1 扩展，模块名为 `wasi_snapshot_preview1`，导入名带有 `_wasm64` 后缀。运行程序需要 VM 实现该扩展并授予程序实际请求的导入。
