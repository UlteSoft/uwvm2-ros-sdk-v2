# nvidia-isaac-sim 只读观测

`Isaac Sim ROS2 Publish Clock / rosgraph_msgs/Clock`。读取 Isaac Sim ROS2 Publish Clock 图节点输出的时钟消息。该节点的 timeStamp 输入以秒为单位。

输入为含封装头的 ROS 2 CDR1 消息，支持大端和小端。可读取的字段函数为 `read_clock_sec`、`read_clock_nanosec`。

C 包含 `<uwrosv2/nvidia_isaac_sim/observation.h>`，函数带 `uwrosv2_nvidia_isaac_sim_` 前缀。
C++98 及后续标准包含 `<uwrosv2/nvidia_isaac_sim/observation.hpp>`，使用 `uwrosv2::nvidia_isaac_sim` 命名空间。
C 函数接受输出指针，C++ 函数接受输出引用。解码成功时才写入输出。Rust 的 `wros_observation` crate 返回 `Option<T>`。
JS 和 TypeScript 从 `uwrosv2/platform/nvidia-isaac-sim/observation` 导入函数，传入 `Uint8Array`。64 位整数返回 `bigint`，无效记录返回 `undefined`。
AssemblyScript 在有界驱动模式下读取请求暂存区，传入最后一个参数 true 可读取上一次成功回复。读取成功时返回 true，并更新同名字段值。
WAT 库 `include/u2rosv2/platform/nvidia-isaac-sim/wat/observation.wat` 导出线性内存和上述函数。传入输入地址、长度、数组索引（如适用）和输出地址。成功返回 1，并将字段按原宽度以小端序写入。

## 在本地运行

安装时指定 `--platform nvidia-isaac-sim` 和语言，将 `examples/nvidia-isaac-sim/<language>` 复制到用户工程，设置 `UWVM_ROS_SDK_ROOT`、`WROS_VM`。
执行 `xmake build` 和 `xmake test -j1`。示例使用按原始定义构造的离线样本，校验字段值并拒绝截断数据。

## 上游定义

- [source/extensions/isaacsim.ros2.nodes/nodes/OgnROS2PublishClock.ogn](https://github.com/isaac-sim/IsaacSim/blob/87c95274f50836068b44eeb030bf62aa2108bdf8/source/extensions/isaacsim.ros2.nodes/nodes/OgnROS2PublishClock.ogn)
- [rosgraph_msgs/msg/Clock.msg](https://github.com/ros2/rcl_interfaces/blob/7aa3caf43377ea6ad615bc1040832e2c7566bfbe/rosgraph_msgs/msg/Clock.msg)
- [builtin_interfaces/msg/Time.msg](https://github.com/ros2/rcl_interfaces/blob/7aa3caf43377ea6ad615bc1040832e2c7566bfbe/builtin_interfaces/msg/Time.msg)

platform.json 记录各定义文件的 SHA-256 和源码版本。
