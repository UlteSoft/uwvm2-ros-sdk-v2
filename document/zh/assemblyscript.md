# AssemblyScript 标量 Wasm

[English](../en/assemblyscript.md)

`wras` 在 Linux x86-64 构建主机上把 AssemblyScript 直接编译为 core Wasm。SDK 随包提供正式发布的 AssemblyScript 0.28.20、Binaryen 131.0.0 和 Long 5.3.2，固定上游包的完整性校验和实际构建输入。[AssemblyScript 发布页](https://github.com/AssemblyScript/assemblyscript/releases/tag/v0.28.20) · [编译器输入](../../third-parties/assemblyscript/release.json)

## 安装与构建

将 `REV` 设为需要安装的 SDK 提交，将 `WROS_VM` 设为运行 Xmake 测试的 VM 路径。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language as --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT=/absolute/path/printed/by/the/installer
cd "$UWVM_ROS_SDK_ROOT/examples/platform/unitree/common/as"
xmake build
xmake test -j1
```

也可以直接编译一个 `.ts` 文件，程序入口须导出 `_start(): void`。该示例显式请求只读的 `uwvm_ros_v2.abi` 导入，Xmake 本地测试会为被测模块单独授权。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wras" controller.ts --ros-abi --build-receipt -o controller.wasm
```

`--build-receipt` 生成 `controller.wasm.wros-as.json`，其中记录源码和 Wasm 摘要、编译器版本以及 MTE 选项。`-g` 请求上游调试符号名。Xmake 配置支持 `core = "3.0"`、`eh = false` 和可选 MTE 设置。此版本使用固定的优化器配置。

## 支持范围

开发包支持单文件 wasm32 应用中的标量函数和控制流。默认 MTE 配置要求检查最终二进制，证明它没有线性内存、内存导入或数据段。可以用 `--no-mte` 显式修改 MTE 请求值，源码支持范围相同。`--ros-abi` 只允许签名精确匹配的 `uwvm_ros_v2.abi`，省略该参数时模块必须没有导入。

每个平台的安装包也提供 `examples/platform/<platform>/migration/as`，演示如何移植 ROS Noetic Costmap2D 的无符号栅格索引。在目录内运行 `xmake build` 和 `xmake test -j1`，两个 VM 引擎都会测试行边界、回绕和固定种子的输入。生成的 Wasm 无导入。调用者用该索引访问栅格时，须确保坐标有效。[ROS Noetic Costmap2D 源码](https://github.com/ros-planning/navigation/blob/f44bb1fc2810399165115cc98b530fe4b9397c18/costmap_2d/include/costmap_2d/costmap_2d.h)

托管对象、完整 AssemblyScript 运行时、wasm64、线程、异常处理和厂商专属操作仍待支持。
