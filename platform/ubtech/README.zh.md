# ubtech 只读观测

`grab_demo_msgs/GraspCandidate`。读取感知节点报告的检测置信度及候选位置的高度，校验两个带时间戳的坐标系以及分组、类别字符串。

输入为含封装头的 ROS 2 CDR1 消息，支持大端和小端。可读取的字段函数为 `read_confidence`、`read_pose_pose_position_z`。

C 包含 `<uwrosv2/ubtech/observation.h>`，函数带 `uwrosv2_ubtech_` 前缀。
C++98 及后续标准包含 `<uwrosv2/ubtech/observation.hpp>`，使用 `uwrosv2::ubtech` 命名空间。
C 函数接受输出指针，C++ 函数接受输出引用。解码成功时才写入输出。Rust 的 `wros_observation` crate 返回 `Option<T>`。
JS 和 TypeScript 从 `uwrosv2/platform/ubtech/observation` 导入函数，传入 `Uint8Array`。64 位整数返回 `bigint`，无效记录返回 `undefined`。
AssemblyScript 在有界驱动模式下读取请求暂存区，传入最后一个参数 true 可读取上一次成功回复。读取成功时返回 true，并更新同名字段值。
WAT 库 `include/u2rosv2/platform/ubtech/wat/observation.wat` 导出线性内存和上述函数。传入输入地址、长度、数组索引（如适用）和输出地址。成功返回 1，并将字段按原宽度以小端序写入。

## 在本地运行

安装时指定 `--platform ubtech` 和语言，将 `examples/ubtech/<language>` 复制到用户工程，设置 `UWVM_ROS_SDK_ROOT`、`WROS_VM`。
执行 `xmake build` 和 `xmake test -j1`。示例使用按原始定义构造的离线样本，校验字段值并拒绝截断数据。

## 上游定义

- [src/grab_demo_msgs/msg/GraspCandidate.msg](https://github.com/UBTECH-Robot/tk_sdk_demo/blob/3df9f9dc7689203fb673a21d8205bb597ed4fafe/src/grab_demo_msgs/msg/GraspCandidate.msg)
- [std_msgs/msg/Header.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/std_msgs/msg/Header.msg)
- [builtin_interfaces/msg/Time.msg](https://github.com/ros2/rcl_interfaces/blob/7aa3caf43377ea6ad615bc1040832e2c7566bfbe/builtin_interfaces/msg/Time.msg)
- [geometry_msgs/msg/PoseStamped.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/PoseStamped.msg)
- [geometry_msgs/msg/Pose.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/Pose.msg)
- [geometry_msgs/msg/Point.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/Point.msg)
- [geometry_msgs/msg/Quaternion.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/Quaternion.msg)

platform.json 记录各定义文件的 SHA-256 和源码版本。
