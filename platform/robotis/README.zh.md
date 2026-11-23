# robotis 只读观测

`turtlebot3_msgs/SensorState`。从含可变长度消息头的 TurtleBot3 状态中读取碰撞开关位掩码、带符号轮编码器和电池字段。

输入为从第一个字段开始的 ROS 1 紧凑序列化消息正文。可读取的字段函数为 `read_bumper`、`read_left_encoder`、`read_right_encoder`、`read_battery`。

C 包含 `<uwrosv2/robotis/observation.h>`，函数带 `uwrosv2_robotis_` 前缀。
C++98 及后续标准包含 `<uwrosv2/robotis/observation.hpp>`，使用 `uwrosv2::robotis` 命名空间。
C 函数接受输出指针，C++ 函数接受输出引用。解码成功时才写入输出。Rust 的 `wros_observation` crate 返回 `Option<T>`。
JS 和 TypeScript 从 `uwrosv2/platform/robotis/observation` 导入函数，传入 `Uint8Array`。64 位整数返回 `bigint`，无效记录返回 `undefined`。
AssemblyScript 在有界驱动模式下读取请求暂存区，传入最后一个参数 true 可读取上一次成功回复。读取成功时返回 true，并更新同名字段值。
WAT 库 `include/u2rosv2/platform/robotis/wat/observation.wat` 导出线性内存和上述函数。传入输入地址、长度、数组索引（如适用）和输出地址。成功返回 1，并将字段按原宽度以小端序写入。

## 在本地运行

安装时指定 `--platform robotis` 和语言，将 `examples/robotis/<language>` 复制到用户工程，设置 `UWVM_ROS_SDK_ROOT`、`WROS_VM`。
执行 `xmake build` 和 `xmake test -j1`。示例使用按原始定义构造的离线样本，校验字段值并拒绝截断数据。

## 上游定义

- [msg/SensorState.msg](https://github.com/ROBOTIS-GIT/turtlebot3_msgs/blob/76e78b0a34e07cf1dd16dafdc54c44f35c5b83eb/msg/SensorState.msg)
- [msg/Header.msg](https://github.com/ros/std_msgs/blob/34198520757d1aab358118a0ef294fe2609fde33/msg/Header.msg)

platform.json 记录各定义文件的 SHA-256 和源码版本。
