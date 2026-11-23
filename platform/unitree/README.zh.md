# 读取 Unitree Go2 低层状态

`unitree` 选择提供 `go2-state` 只读驱动契约。提供方读取 DDS 的 `rt/lowstate`，返回采样 tick 以及第一个关节的 binary32 位置。离线示例在 VM 内解码录制值 41347 和 0.125。读取实时数据需要部署方提供匹配的驱动、连接及场景能力。[固定版本的提供方契约](https://github.com/UlteSoft/wasmros-deployer/blob/69e5e1be8fe3d669af962e5f63c147959ec45ad7/tests/support/unitree_low_state_contract.txt)

guest 提交六个小端 u64，依次为序列号、单调时钟截止时间（纳秒）、负载长度 24、缓冲区句柄 1、偏移 0、请求长度 16。成功的 `driver.result` 共 40 字节，依次返回状态 0、主体长度 24、缓冲区长度 16、采样 tick、关节位置位模式。各语言的解码器均检查两层长度、32 位 tick 和有限的 binary32 关节位置。[固定版本的 WAT 调用示例](https://github.com/UlteSoft/wasmros-deployer/blob/69e5e1be8fe3d669af962e5f63c147959ec45ad7/tests/support/unitree_low_state.wat)

JavaScript 和 TypeScript 从 `uwrosv2/platform/unitree/go2_low_state` 导入 `encode_read` 和 `decode_result`。向 `decode_result` 传入 `Uint8Array`，读取字段前先检查返回值是否为 `undefined`。AssemblyScript 在有界驱动模式下从 `./uwrosv2/platform/unitree/go2_low_state` 导入两个函数，解码成功时更新 `tick` 和 `first_joint_position`。WAT 库 `include/u2rosv2/platform/unitree/wat/go2_low_state.wat` 导出内存和两个函数，解码时需提供可读输入区及 8 字节可写输出区。

将安装目录内的 `examples/unitree/<language>` 复制到自己的工程目录，设置 `UWVM_ROS_SDK_ROOT` 与 `WROS_VM`，然后执行 `xmake build` 和 `xmake test -j1`。

Python 选择提供 Unitree ROS 2 v0.3.0 的 `unitree_api`、`unitree_go` 与 `unitree_hg` 消息类。示例直接解码 Fast-CDR 生成的完整 Go2 与 HG LowState 帧。Go2 的 `temperature_ntc1` 和 `temperature_ntc2` 在 ROS 2 里为有符号八位数，在 SDK2 C++ 声明里为无符号字节。[Python 工程、安装与验证](../../document/zh/languages/py.md)
