# 独立 Zig 控制器

选择目标平台并安装 `zig` 开发包。该驱动把单个 Zig 0.16.0
源码文件经 SDK 的 WasmMTE 后端编译为 Core WebAssembly 3.0。
配置支持 wasm32、wasm64、单线程、Zig 错误联合和独立应用。
通过 `const scene = @import("wros_scene.zig");`
使用生成的绑定，例如 `scene.wr_abi()`。`wrzig` 从已安装 SDK 载入绑定模块。
函数参数和返回类型与 ROSv2 ABI 目录中的固定宽度签名一致。

宽整数操作可从所选 sysroot 中已校验的 compiler-rt 内建函数归档解析。
目前不提供 WASI 导入、可选目标 intrinsic、内联汇编、动态加载或原生依赖。
Zig 堆分配器、多线程和依赖 libc 的应用需要
单独认证的闭包。未解析的运行时符号会导致构建失败。Zig 前端以保留检查的
调试语义生成 IR，再由 SDK 后端执行 `-O3` 并保留 `-g` 调试信息。

准备对应地址宽度的无 EH 后端工具链和 sysroot。把官方 Linux x86-64 归档
`zig-x86_64-linux-0.16.0.tar.xz` 放入
`TOOLCHAIN/share/wros/zig/`。驱动验证发行摘要后，在私有工作目录解包
编译器和标准库源码。用同一 SDK 版本编译 IR 工具：

```sh
python3 language/zig/prepare.py --toolchain "$TOOLCHAIN" --host-cxx /usr/bin/c++
```

IR 工具拒绝汇编、外部全局存储、线程设施和绕过插桩的属性。
LLVM 降低模块前，对受支持的函数和可寻址全局对象加标记，包括只读数据。
输出前检查内存上限，以及 `uwvm_ros_v2` 导入的准确名称与类型。

默认构建须通过本地 WSEA 站点验证。声明绑定一个地址宽度、SDK 和编译输入，
以及通过独立测试的 VM。`tests/zig_site.py` 使用一次性测试证书验证该流程。
生产站点由操作员审阅并签名。安装时向 `bootstrap.py install`
传入 `--site-profile`，然后编译控制器：

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrzig" controller.zig -o controller.wasm --build-receipt
```

开发包含目标平台的通用、扩展和 Noetic 索引移植示例。进入示例目录，
执行 `xmake f -p wasm-wasip1 -a wasm32` 和 `xmake build`，
再执行 `WROS_VM=/绝对路径/uwvm2-ros xmake test -j1`。
选用另行签名的 wasm64 站点时，把架构改为 `wasm64`。
扩展项目测试平台驱动连接上的两项独立授权。构建本身不授予任何访问权限。

显式无标签构建使用 `--no-mte --toolchain TOOLCHAIN --sysroots UNTAGGED_MANIFEST`。
回执记录该选择，带签名的 `wrzig verify` 部署验证不会接受该模式。
默认构建遇到缺失、错误或失效的签名站点直接退出。

[Zig 官方归档及摘要](https://ziglang.org/download/)
