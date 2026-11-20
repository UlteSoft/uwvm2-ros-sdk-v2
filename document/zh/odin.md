# Odin 独立 wasm32

[English](../en/odin.md)

`wrodin` 把单文件 Odin 应用编译为 core Wasm 3.0。Linux x86-64 编译器由 Odin 官方月度标签 `dev-2026-11a` 的源码通过上游 `make release` 重建，版本显示为 `dev-2026-11:9a69916`，依赖系统的 `libLLVM.so.20.1`。Odin 1.0 GA 不在本次发布范围内。 [上游发布](https://github.com/odin-lang/Odin/releases/tag/dev-2026-11a) · [编译器输入](../../third-parties/odin/release.json)

## 安装与运行

使用安装器输出的绝对路径，并选择 SDK C 编译器配套的 wasm32 无异常、带 MTE 的 sysroot 记录。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language odin --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT=/absolute/path/printed/by/the/installer
export WROS_TOOLCHAIN=/absolute/path/to/paired/sdk/llvm/toolchain
export WROS_SYSROOTS=/absolute/path/to/wasm32/noeh/tagged/sysroots.json
export WROS_VM=/absolute/path/to/uwvm2-ros
cd "$UWVM_ROS_SDK_ROOT/examples/platform/unitree/common/odin"
xmake build
xmake test -j1
```

通用工程在显式授权后检查 ROSv2 ABI，并运行使用栈内存的传感器样例。各平台的 `examples/platform/<platform>/migration/odin` 还包含 ROS Noetic Costmap2D 无符号栅格索引移植，该模块无宿主导入。两类工程都注册了 INT 和 AOT 测试。 [Noetic Costmap2D 源码](https://github.com/ros-planning/navigation/blob/f44bb1fc2810399165115cc98b530fe4b9397c18/costmap_2d/include/costmap_2d/costmap_2d.h)

## 构建选项

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrodin" controller.odin --ros-abi \
  --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --build-receipt -o controller.wasm
```

源码须导出 `_start() -> ()`。指定 `--ros-abi` 时只允许精确匹配的 `uwvm_ros_v2.abi`，省略时导入列表必须为空。导入声明本身不授予运行时权限。编译使用 SDK 的 LLVM 后端和 `-O3 -g`，默认启用 MTE。显式关闭时，直接编译用 `--no-mte` 及匹配的编译器和未标记 sysroot。Xmake 使用 `mte = false` 和 `WROS_SYSROOTS_NO_MTE`。可选构建记录包含配置、源码摘要和编译器输入。

当前提供基础运行库以及单编译单元内经后端支持的栈与全局存储。堆分配、通用 Odin 标准库、线程、异常、真 memory64、对象相邻标签完整鉴定和厂商专属运行仍不在此开发配置中。上游 `wasm64p32` 保留 32 位指针。带标签栈所有权的函数若包含后端无法分类的宿主调用，编译会被拒绝。示例把使用栈内存的计算放在单独的函数中。

安装时选用 `compiler-source` 组件，可按需同时拉取固定版本的 Odin 构建文件和基础运行库源码。宿主 LLVM 的版本和其余构建输入见编译器清单及标记器源码。
