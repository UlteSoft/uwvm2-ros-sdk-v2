# WebAssembly 文本

[English](../en/wat.md)

`wrwat` 在 Linux x86-64 构建主机上汇编和验证 core Wasm。SDK 工具基于 wasm-tools 1.263.0 和固定版本的 WasmMTE 验证器，支持 VM 的线性内存标记编码。安装器校验汇编器归档的摘要。通过 `-- --component compiler-source` 可安装锁定源码和离线重建脚本。 [上游发布页](https://github.com/bytecodealliance/wasm-tools/releases/tag/v1.263.0)

## 安装与构建

将 `REV` 设为要安装的 SDK 提交，将 `WROS_VM` 设为本地测试 VM 的绝对路径。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language wat --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT=/absolute/path/printed/by/the/installer
cd "$UWVM_ROS_SDK_ROOT/examples/platform/unitree/common/wat"
xmake build
xmake test -j1
"$UWVM_ROS_SDK_ROOT/bin/wrwat" controller.wat --ros-operation abi -g --build-receipt -o controller.wasm
```

`--core mvp` 选择 MVP 指令集，默认采用 `--core 3.0`。默认目标为 `wasm32`，`--target wasm64` 允许 64 位内存和表编码。Core 3.0 默认接受其标准异常处理，`--no-eh` 会拒绝异常指令和标记。`--threads` 允许共享内存和原子指令。带线程的 wasm32 模块通过 `--shared-memory MODULE FIELD` 选择一个具有上限的共享内存导入后，也可以导入签名精确匹配的 `wasi.thread-spawn(i32) -> i32`。运行时仍需给该模块独立配置 I1T 权限和线程执行预算。本汇编器拒绝 Preview1 导入。

默认允许 MTE 语法，普通内存声明和指令照常汇编。在 WAT 中显式编写需要的分配和标记操作。例如 `(memtag.claim $heap (i32.const 128) (i32.const 16))` 按所选内存的地址宽度解析操作数，并按实际内存索引生成 VM 指令。支持折叠和扁平堆栈写法。二进制验证器检查每条指令的立即数和操作数类型，内存生命周期与指针用法由 WAT 源码决定。验证器也会检查 `uwvm.memtag.linear.globals` 自定义段中的第 2 版静态标记注册。

通过托管指令取得分配后，VM 排除近邻分配已使用的标签，再从允许的标签中选择。汇编器不参与分配标签。`--no-mte` 或 Xmake 的 `mte = false` 允许使用原始内存，构建时会拒绝显式 MTE 指令。对已经含有标记指令的 Wasm，可通过 VM 的 `--runtime-disable-memtag` 独立关闭运行时的标记执行。

每个需要导入的 ROS 操作须通过 `--ros-operation NAME` 声明。Xmake 使用 `add_wros_operations`。最终 ROS 导入集合和签名必须与声明及已安装的 ROSv2 ABI 精确匹配，运行权限由 VM 单独控制。构建拒绝组件二进制及 Component Model 接口约定。`-g` 或 Xmake `set_symbols("debug")` 从 WAT 生成 DWARF，源码名保留原文件的基本名称。`--build-receipt` 或 Xmake `build_receipt = true` 可记录源码、产物和汇编器摘要以及所选配置。

安装包中的 `examples/wat/thread-mte` 可构建共享内存所有者与带标记的访客模块。把 `WROS_PLATFORM` 设置成已安装的平台，执行 `xmake f -p wasm-wasip1-threads -a wasm32`。工程用 `set_wros_wat_shared_memory("env", "memory")` 声明所有者。SDK 的 `tests/wat_thread_mte.py` 在仅授予一个子线程的 VM 中验证该工程，并单独检查默认拒绝。

## 自带示例

每个平台安装后的 `examples/platform/<platform>` 包含以下工程。

- `common/wat` 测试只读 ROSv2 ABI 查询和定宽整数运算。
- `migration/wat` 验证 ROS Noetic Costmap2D 的无符号行优先索引。 [上游实现](https://github.com/ros-planning/navigation/blob/f44bb1fc2810399165115cc98b530fe4b9397c18/costmap_2d/include/costmap_2d/costmap_2d.h)
- `extension/wat` 使用一页私有缓冲区并显式关闭 MTE。两种拒绝测试分别验证父级权限与平台权限的缺失会阻止连接，且回复缓冲区保持原值。测试采用私有套接字对。
