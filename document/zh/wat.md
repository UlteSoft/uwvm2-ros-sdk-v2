# WebAssembly 文本

[English](../en/wat.md)

`wrwat` 将 WAT 汇编为 core Wasm。开发包附带 Linux x86-64 构建主机所用的正式版 wasm-tools 1.263.0，并在使用前验证发布方提供的 SHA-256。入口提供汇编和验证功能。 [上游发布页](https://github.com/bytecodealliance/wasm-tools/releases/tag/v1.263.0)

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

`--core mvp` 选择 MVP 指令集，默认采用 `--core 3.0`。默认目标为 `wasm32`，`--target wasm64` 允许 64 位内存和表编码。Core 3.0 默认接受其标准异常处理，`--no-eh` 会拒绝异常指令和标记。Core 3.0 下的 `--threads` 允许共享内存和原子指令。汇编器的宿主导入规则不提供 Wasm 线程创建或 WASI 导入。

默认 MTE 配置要求最终模块无线性内存及数据段，汇编器直接检查产物。该配置支持有类型的栈值、全局变量、表以及所选的 core 特性。若模块使用原始线性内存，需显式传入 `--no-mte`，或在 Xmake 配置中设置 `mte = false`。汇编器不会给手写内存操作自动插入 WasmMTE 指令。

每个需要导入的操作须通过 `--ros-operation NAME` 声明。Xmake 使用 `add_wros_operations`。最终导入集合和签名必须与声明及已安装的 ROSv2 ABI 精确匹配，运行权限由 VM 单独控制。构建拒绝 WASI 导入、组件二进制及 Component Model 接口约定。`-g` 或 Xmake `set_symbols("debug")` 从 WAT 生成 DWARF，源码名保留原文件的基本名称。`--build-receipt` 或 Xmake `build_receipt = true` 可记录源码、产物和汇编器摘要以及所选配置。

## 自带示例

每个平台安装后的 `examples/platform/<platform>` 包含以下工程。

- `common/wat` 测试只读 ROSv2 ABI 查询和定宽整数运算。
- `migration/wat` 验证 ROS Noetic Costmap2D 的无符号行优先索引。 [上游实现](https://github.com/ros-planning/navigation/blob/f44bb1fc2810399165115cc98b530fe4b9397c18/costmap_2d/include/costmap_2d/costmap_2d.h)
- `extension/wat` 使用一页私有缓冲区并显式关闭 MTE。两种拒绝测试分别验证父级权限与平台权限的缺失会阻止连接，且回复缓冲区保持原值。测试采用私有套接字对。
