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

## MuJoCo 仿真

源码仓库中的复跑脚本使用选择式安装的 `wras` 构建控制器。生成的
控制器没有导入或线性内存，UWVM 使用明确的模块名预加载它。独立的
WAT 主模块调用标量导出 `jointTarget`，将返回值编码后通过自己的
ROSv2 驱动权限提交。两个模块都关闭 WASIp1，仅 WAT 主模块获得场景授权。

在 SDK 源码仓库下使用现有的 64 GiB、零 swap 门禁。提前设置对应的
VM 源码及二进制、官方 MuJoCo、VM 的 OpenSSL 前缀和上游模型资产路径。

```sh
PATH_TO_GATE python3 -B tests/assemblyscript_mujoco.py \
    --commit "$REV" --vm-source "$VM_SOURCE" --runtime "$VM" \
    --mujoco "$MUJOCO" --openssl-root "$OPENSSL_PREFIX" \
    --vendor-model "$VM_SOURCE/test/0084.ros-runtime/mujoco_profiles/unitree-go2.json" \
    --vendor-assets "$GO2_ASSETS" --output .tmp/assemblyscript-go2
```

脚本将 128 个仿真步与直接调用原生 MuJoCo 的结果比对，也检查越界命令
不推进仿真，以及外部接收器在执行一步后崩溃时 VM 仍能查询故障状态并断连。
收据记录 INT 和 AOT 各自的三项用例、模型资产、构建摘要和驱动调用审计。
