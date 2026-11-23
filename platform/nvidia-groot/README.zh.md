# nvidia-groot 只读观测

`DROID observation.state`。读取 GR00T 演示数据集中的一行 DROID 状态。传入已解出的 17 个小端 float32。末端执行器占 [0,9)，夹爪占 [9,10)，七个关节占 [10,17)。

输入为上述字段或记录的小端字节序列。可读取的字段函数为 `read_eef_9d`、`read_gripper_position`、`read_joint_position`。

C 包含 `<uwrosv2/nvidia_groot/observation.h>`，函数带 `uwrosv2_nvidia_groot_` 前缀。
C++98 及后续标准包含 `<uwrosv2/nvidia_groot/observation.hpp>`，使用 `uwrosv2::nvidia_groot` 命名空间。
C 函数接受输出指针，C++ 函数接受输出引用。解码成功时才写入输出。Rust 的 `wros_observation` crate 返回 `Option<T>`。
JS 和 TypeScript 从 `uwrosv2/platform/nvidia-groot/observation` 导入函数，传入 `Uint8Array`。64 位整数返回 `bigint`，无效记录返回 `undefined`。
AssemblyScript 在有界驱动模式下读取请求暂存区，传入最后一个参数 true 可读取上一次成功回复。读取成功时返回 true，并更新同名字段值。
WAT 库 `include/u2rosv2/platform/nvidia-groot/wat/observation.wat` 导出线性内存和上述函数。传入输入地址、长度、数组索引（如适用）和输出地址。成功返回 1，并将字段按原宽度以小端序写入。

## 在本地运行

安装时指定 `--platform nvidia-groot` 和语言，将 `examples/nvidia-groot/<language>` 复制到用户工程，设置 `UWVM_ROS_SDK_ROOT`、`WROS_VM`。
执行 `xmake build` 和 `xmake test -j1`。示例使用按原始定义构造的离线样本，校验字段值并拒绝截断数据。

## 上游定义

- [demo_data/droid_sample/meta/modality.json](https://github.com/NVIDIA/Isaac-GR00T/blob/dac54b313160c201c450f97df0fd74ebd379c892/demo_data/droid_sample/meta/modality.json)
- [demo_data/droid_sample/meta/info.json](https://github.com/NVIDIA/Isaac-GR00T/blob/dac54b313160c201c450f97df0fd74ebd379c892/demo_data/droid_sample/meta/info.json)

platform.json 记录各定义文件的 SHA-256 和源码版本。
