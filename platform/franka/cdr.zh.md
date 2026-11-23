# Franka ROS 2 CDR 记录

C、C++、Rust 和 Go 分别实现 137 个类型化 XCDRv1 PLAIN_CDR 记录的编解码。Franka ROS 2 3.6.0 的机械臂和夹爪包提供 18 份定义，展开为 77 个记录。脊柱包提供 12 份定义，展开为 35 个记录。七个标准 ROS 2 依赖包另提供 25 个记录。C、C++ 和 Rust 使用调用者提供的存储。标准 Go 和 TinyGo 共享同一个模块，解码后的字符串和切片独立持有数据。编解码在本地缓冲区中进行。[机械臂和夹爪接口](https://github.com/frankarobotics/franka_ros2/tree/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_msgs) · [脊柱接口](https://github.com/frankarobotics/franka_ros2/tree/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_spine/franka_spine_msgs)

## 接口范围

- 机械臂和夹爪消息为 `CollisionIndicators`、`Elbow`、`Errors`、`FrankaRobotState`、`GraspEpsilon`、`TargetStatus`。服务为 `SetCartesianStiffness`、`SetForceTorqueCollisionBehavior`、`SetFullCollisionBehavior`、`SetJointStiffness`、`SetLoad`、`SetStiffnessFrame`、`SetTCPFrame`。动作为 `ErrorRecovery`、`Grasp`、`Homing`、`Move`、`PTPMotion`。[上游机械臂 CMake 清单](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_msgs/CMakeLists.txt)
- 脊柱消息为 `SpineParameters`、`SpinePosition`、`SpineState`、`UserLimits`。服务为 `FaultReset`、`GetParameters`、`GetPosition`、`GetSpineState`、`Halt`、`SwitchOff`、`SwitchOn`。动作为 `MoveAbsolute`。[上游脊柱 CMake 清单](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_spine/franka_spine_msgs/CMakeLists.txt)
- 每个服务都有请求、响应和自省事件。每个动作都有目标、结果、反馈，分别用于 SendGoal 和 GetResult 服务的请求、响应和事件，以及 FeedbackMessage 消息。标准依赖包括动作状态和取消、时间、消息头、关节状态、服务事件、几何量及 UUID。组件保留上游后缀，例如 `PTPMotion_SendGoal_Request`。每个包均有对应的原生头文件、Rust 模块和 Go 包。[Jazzy rosidl 服务和动作定义](https://github.com/ros2/rosidl/blob/9bcfabf3eddf8e63fb4332dca6da7ec6f3140d65/rosidl_parser/rosidl_parser/definition.py)
- C、C++、Rust、JavaScript、TypeScript、AssemblyScript 和 WAT 的只读观测函数均可读取 Elbow 五个数组的任一分量。C、C++、Rust 和 Go 提供全部类型化记录及其编码器。[Elbow 定义](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_msgs/msg/Elbow.msg)

## 帧和字段

输入以四字节封装头开始，标识符 0 为大端，1 为小端。标量从封装头之后开始对齐，嵌套记录沿用同一个对齐原点。定长数组按声明顺序存放全部元素，动态序列先写 uint32 元素数。服务事件的请求与响应序列分别容纳零个或一个元素。字符串以 uint32 记录包含末尾 NUL 的字节数，公开视图只包含正文。常量不占用帧空间。上游 rosidl 为每个空结构增加一个 uint8 占位字段，其默认值为零。[rosidl 结构模板](https://github.com/ros2/rosidl/blob/9bcfabf3eddf8e63fb4332dca6da7ec6f3140d65/rosidl_adapter/rosidl_adapter/resource/struct.idl.em) · [Fast-CDR 实现](https://github.com/eProsima/Fast-CDR/blob/9f4e60f7ac958e0fbbfe949102de3929cbbc226f/src/cpp/Cdr.cpp)

解码会校验整帧，包括嵌套长度、值为 0 或 1 的布尔量、字符串末尾的 NUL 和序列上界。编码时对齐填充和封装选项均写零。读取时接受零选项，也接受低两位声明的尾部填充，但声明数量必须与实际载荷长度的四字节对齐要求一致。传输层可以保留或剥除这些已声明的填充。多余的其他字节会被拒绝。

Elbow 的三个位置数组中，第一个分量为第 3 关节的弧度值，第二个为第 4 关节相对翻转角的符号。命令速度和加速度的第一个分量用 rad/s 和 rad/s² 表示，libfranka 将这两个数组的第二个分量置零。脊柱绝对运动以米表示位置，并要求速度、加速度和减速度为正。编解码器校验载荷结构，上游服务端负责执行条件和权限判断。guest 可在空平台能力列表下构造、读取和转码消息。[libfranka 机器人状态](https://github.com/frankarobotics/libfranka/blob/3cc708cafa1cdba49ceaab536a14216dfb7bf48a/include/franka/robot_state.h) · [MoveAbsolute 动作](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_spine/franka_spine_msgs/action/MoveAbsolute.action)

## C

包含 `<uwrosv2/franka/cdr/records.h>` 或单包头文件，例如 `<uwrosv2/franka/cdr/franka_msgs.h>`。类型名由 `uwrosv2_franka_cdr_`、包名和组件名组成，例如 `uwrosv2_franka_cdr_franka_msgs_Elbow`。类型的 `_DATATYPE` 宏给出完整 ROS 名称。

- `T_defaults()` 应用声明中的默认值，并递归初始化嵌套记录，例如 0.005 m 的夹爪容差和单位四元数。
- `T_encoded_size(&value, &size)` 给出含封装头的总长度。`T_encode(&value, order, dst, capacity, &written)` 选择 `uwrosv2_franka_cdr_big_endian` 或 `uwrosv2_franka_cdr_little_endian`。
- `T_decode(src, size, &value)` 在整帧合法时写入输出。`T_validate(src, size)` 仅校验整帧。这些操作成功返回 1，失败返回 0。
- 双精度序列用 `uwrosv2_franka_cdr_float64_sequence_values(data, count)` 构造。可读取 `count`，用 `_sequence_iter(&seq)` 获取迭代器，再用 `_sequence_next(&iter, &value)` 读取元素。记录序列使用对应记录的类型名前缀。

## C++98 至 C++26

包含 `<uwrosv2/franka/cdr/records.hpp>`，可声明 `namespace cdr = uwrosv2::franka::cdr;`。类型使用包命名空间，例如 `cdr::franka_msgs::Elbow`。用 `T::defaults()` 应用 ROS 声明的默认值。rosidl 的 `T_Constants` 命名空间提供具有原声明整数宽度的常量。记录上也可直接访问常量名，用于整型表达式。服务提供 `Request`、`Response` 和 `Event`。动作聚合各组件和两个服务，例如 `cdr::franka_msgs::PTPMotion::SendGoal::Request`。

使用 `cdr::encoded_size(value, size)`、`cdr::encode(value, cdr::little_endian, dst, capacity, written)`、`cdr::decode(src, size, value)` 和 `cdr::validate<T>(src, size)`，均返回 `bool`。序列可用 `cdr::Sequence<T>::from_values(data, count)` 构造，`seq.size()` 给出元素数。保留 `seq.iter()` 的结果并反复调用其 `next(value)` 可读取所有元素。C++ 独立实现为 C++98/03 使用 `throw()`，从 C++11 起使用 `noexcept`。

C 和 C++ 解码出的字符串和序列借用只读输入帧。迭代、转码等最后一次访问结束前，调用者须保持输入有效且内容稳定。由类型化数组构造的序列也借用该数组。编码器先计算完整长度，再向缓冲区写入。输出缓冲区和长度槽彼此独立，并与输入记录及其借用的所有数据互不重叠。

## Rust

导入 `wros_observation::cdr::{Endian, Message, Sequence}`。记录位于 `wros_observation::cdr::<包名>`，`T::default()` 应用声明的默认值。`T::decode(frame)`、`T::validate(frame)`、`value.encoded_size()` 和 `value.encode(Endian::Big, &mut out)` 返回 `Result`。`Error` 区分封装、填充、截断、额外尾字节、无效布尔量或字符串、序列越界、长度溢出和输出空间不足。

字符串为借用的 `&[u8]`。定长数组为原生 Rust 数组，`Sequence::from_values(&items)` 可从类型化切片构造序列。通过 `seq.len()` 和 `seq.iter()` 遍历。借用字段的生命周期与其来源关联。`Service` 和 `Action` trait 提供组件的关联类型。整个实现使用 `no_std`。

## 标准 Go 和 TinyGo

公共模块为 `github.com/UlteSoft/uwvm2-ros-sdk-v2/franka`。导入该路径下的 `cdr/frankamsgs` 可使用语义组件状态、机械臂和夹爪记录，`cdr/frankaspinemsgs` 提供脊柱记录。`frankamsgs.DefaultFrankaRobotState()` 初始化嵌套位姿四元数，`frankamsgs.DefaultGraspGoal()` 初始化夹爪的内外容差。`MarshalCDR(order, dst)` 可选择大小端序，`MarshalBinary()` 分配小端帧，`UnmarshalCDR(src)` 可读取两种字节序。解码后的值可以在复用输入缓冲区后继续使用。两个示例都是独立的 Go 模块，使用当前 SDK 随包安装的编译器、Xmake 和 VM。[Go/TinyGo 分域 API、字节边界及外部工程](../../include/u2rosv2/platform/franka/go/README.zh.md)

## 离线示例

所选安装包含 `examples/franka/<语言>`。C、C++ 和 Rust 的完整类型化示例在其 `cdr` 子目录。设置 `UWVM_ROS_SDK_ROOT` 和 `WROS_VM` 后，执行 `xmake build` 和 `xmake test -j1`。示例在 guest 内存中双向转码 Elbow，读取 Franka PTPMotion 测试中的七个关节角和速度，并将脊柱 GetPosition 测试中的 0.42 m 响应写入服务事件。[上游 PTPMotion 样本](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_hardware/test/ptp_motion_test.cpp#L147) · [上游脊柱位置样本](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_spine/franka_spine_server/test/test_spine_controller.py#L311)

两条各 84 字节的 Elbow 帧由独立的 eProsima Fast-CDR v2.2.5 生成。诊断样本为每个数组的两个分量赋值，包括两个命令导数的第二分量。源码中的 `src/platform/franka/elbow_fixtures.json` 保存两条帧和各自的 SHA-256。在 SDK 源码根目录执行 `python3 -B src/platform/franka/generate_cdr.py` 可从固定输入重新生成 Franka 绑定和观测示例。[Fast-CDR v2.2.5](https://github.com/eProsima/Fast-CDR/tree/9f4e60f7ac958e0fbbfe949102de3929cbbc226f)
