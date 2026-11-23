# ABB ROS 1 消息和服务正文

C、C++、Rust 和 Go 绑定提供 25 种 ABB 消息、22 组服务请求和响应，以及它们共用的 `std_msgs/Header`。字段、常量、包名和握手 MD5 取自固定版本的上游定义。示例在 guest 内存中交换数据。本次开发环境没有连接真机、ROS master 或 RobotStudio 控制器。[ABB 接口定义](https://github.com/ros-industrial/abb_robot_driver_interfaces/tree/da809cd0bb6f270c0814fca07d7d4a5c0385fc39) · [std_msgs/Header](https://github.com/ros/std_msgs/blob/34198520757d1aab358118a0ef294fe2609fde33/msg/Header.msg)

## 接口范围

- `abb_egm_msgs` 提供 `EGMChannelState` 和 `EGMState`。状态消息包含标准消息头和各 EGM 通道的状态。
- `abb_rapid_msgs` 提供 `ConfData`、`ExtJoint`、`JointTarget`、`LoadData`、`Orient`、`Pos`、`Pose`、`RobJoint`、`RobTarget`、`ToolData` 和 `WObjData`。各字段的 Doxygen 和 Rust 文档保留上游给出的单位和参考坐标系。例如 `RobJoint` 表示相对校准位置的角度，单位为度；外部轴的位置按轴类型使用度或毫米。
- `abb_rapid_sm_addin_msgs` 提供 `EGMActivateSettings`、`EGMRunSettings`、`EGMSettings`、`EGMSetupSettings`、`EGMStopSettings`、`RuntimeState` 和 `StateMachineState`。四种服务为 `GetEGMSettings`、`SetEGMSettings`、`SetRAPIDRoutine` 和 `SetSGCommand`。
- `abb_robot_msgs` 提供 `MechanicalUnitState`、`RAPIDSymbolPath`、`RAPIDTaskState`、`ServiceResponses` 和 `SystemState`。文件内容、I/O 信号、RAPID 的 bool/dnum/num/string/symbol 值以及速度倍率均提供 Get 和 Set 两种服务。另有 `GetRobotControllerDescription` 和 `TriggerWithResultCode`，共计 18 种服务。

## 字节格式与生命周期

从正文第一个字段开始传入字节。定长标量按小端序排列。字符串先写 uint32 字节长度，再写对应的字节，内部允许含零字节。变长数组先写 uint32 元素数量，再依次写入元素。嵌套记录按定义中的字段顺序排列。时间戳使用两个 uint32，依次为秒和纳秒。常量占零字节。`GetSpeedRatioRequest` 等空请求的有效长度为零。TCPROS 连接头、外围长度和服务传输成功标志由传输层处理。[ROS 序列化实现](https://github.com/ros/roscpp_core/blob/noetic-devel/roscpp_serialization/include/ros/serialization.h) · [ROS 服务连接](https://github.com/ros/ros_comm/blob/noetic-devel/clients/roscpp/src/libros/service_client_link.cpp)

解码及校验都会遍历全部字段和数组元素，检查各变长字段的长度，拒绝截断、末尾多余字节和 0、1 之外的布尔字节。整数、时间戳及 IEEE-754 浮点值按原始位模式传递。上游类型文档给出应用约束，例如速度倍率范围为 0 至 100。ROS 字符串常量保留等号右侧去掉首尾空白后的文字，ABB 定义中写出的双引号也属于常量内容。[ROS 常量解析](https://github.com/ros/genmsg/blob/noetic-devel/src/genmsg/msg_loader.py) · [ROS 类型 MD5 算法](https://github.com/ros/genmsg/blob/noetic-devel/src/genmsg/gentools.py)

C、C++ 和 Rust 解码得到的字符串和数组借用输入缓冲区。直到遍历和再次编码等操作全部结束，都须保持该缓冲区有效且内容不变。构造数组时传入类型化的元素数组或切片。三种语言均无须堆分配。编码先检查完整正文长度，再写入缓冲区。C 和 C++ 编码时，应保持输入记录及其借用的数据、输出缓冲区和写入长度变量互不重叠。

## C

包含 `<uwrosv2/abb/ros1/records.h>`。类型名为 `uwrosv2_abb_ros1_` 加上游包名、下划线和记录名。例如，`uwrosv2_abb_ros1_abb_robot_msgs_GetRAPIDNumResponse` 有 `value`、`result_code` 和 `message` 三个字段。附加下列后缀即可得到对应函数，成功返回 1，失败返回 0。

- `_encoded_size(&record, &size)` 计算准确的字节数。
- `_encode(&record, data, capacity, &written)` 写入正文。输入无效或容量不足时，保留缓冲区和计数。
- `_decode(data, size, &record)` 在完整校验通过后写入记录。
- `_validate(data, size)` 校验完整正文。

字符串成员为 `data` 和 `size`。数组元素类型 `T` 提供 `T_array_values(values, count)`、`T_array_iter(&seq)` 和 `T_array_next(&iter, &element)`。`seq.count` 给出元素数量。消息与服务的类型名称和 MD5 宏分别使用 `_DATATYPE` 和 `_MD5` 后缀。

## C++98 至 C++26

包含 `<uwrosv2/abb/ros1/records.hpp>`，可定义别名 `namespace r = uwrosv2::abb::ros1;`。例如 `r::abb_robot_msgs::GetRAPIDNum` 提供 `Request`、`Response`、`datatype()` 和 `md5()`。实现使用独立的 C++ 头文件，C++98/03 使用 `throw()`，从 C++11 起使用 `noexcept`。

调用 `r::encoded_size(record, size)`、`r::encode(record, data, capacity, written)`、`r::decode(data, size, record)` 和 `r::validate<T>(data, size)`，均返回 `bool`，成功后写入结果。`r::Sequence<T>::from_values(values, count)` 借用类型化数组。`seq.iter()` 创建迭代器，可多次调用 `next(element)` 顺序取值。

## Rust

导入 `wros_observation::ros1::Message` 即可使用 `T::decode(data)`、`T::validate(data)`、`record.encoded_size()` 和 `record.encode(&mut bytes)`。返回值为 `Result`，可区分截断、尾部多余数据、非规范布尔值、长度溢出和输出容量不足。字符串类型为 `&[u8]`。变长数组可通过 `Sequence::from_values(&items)` 构造，通过 `.len()` 和 `.iter()` 访问。Rust 生命周期约束借用字段的有效期。`Service` trait 关联每种服务的请求和响应类型、ROS 类型名及 MD5。平台 crate 支持 `no_std`。

## Go 与 TinyGo

模块 `github.com/UlteSoft/uwvm2-ros-sdk-v2/abb` 按上游接口拆分为五个包。每种记录都有 `ROS1Size`、`MarshalROS1`、`UnmarshalROS1`，并实现 Go 标准库的二进制编解码接口。解码后的字符串和切片拥有独立存储。安装后可直接复制 `examples/abb/go` 或 `examples/abb/tinygo` 到外部工程。[分域接口、缓冲区与构建指南（英文）](../../include/u2rosv2/platform/abb/go/README.md)

## 读取 RAPID 数值

RWS 服务提供者在其服务命名空间注册 `get_rapid_num`。`GetRAPIDNumRequest` 内的 `RAPIDSymbolPath` 包含任务名、模块名和符号名三个字符串。响应包含 float32 数值、uint16 结果码和状态消息。先判断结果码，再使用成功响应中的数值。数值 12.5、成功码 1、空状态消息的完整正文为十字节 `00 00 48 41 01 00 00 00 00 00`。[ABB 服务定义](https://github.com/ros-industrial/abb_robot_driver_interfaces/blob/da809cd0bb6f270c0814fca07d7d4a5c0385fc39/abb_robot_msgs/srv/GetRAPIDNum.srv) · [RWS 服务注册](https://github.com/ros-industrial/abb_robot_driver/blob/d1678957d3792e6aa54582ff894db62b6a51dac0/abb_rws_service_provider/src/rws_service_provider.cpp#L143)

安装 ABB 平台的 `c`、`cpp` 或 `rust` 绑定后，打开 `examples/abb/<language>/ros1` 中的 Xmake 工程。示例在调用方编码请求，在本地处理函数解码并返回样例数值，再由调用方解码响应。随后示例构造带标准消息头的 `SystemState`，遍历 RAPID 任务和机械单元两个数组。仓库中的示例位于 `src/examples/abb/<language>/ros1`。
