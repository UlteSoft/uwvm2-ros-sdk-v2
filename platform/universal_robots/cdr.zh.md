# Universal Robots 仪表板消息

C、C++ 和 Rust 提供 Universal Robots ROS 2 Driver 7.3.0 在 `ur_dashboard_msgs` 注册的全部 8 种普通消息，每种均可在内存中按 XCDRv1 编解码。上游提交为 `9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8`，共 16 个字段、57 个具名常量。该包的 25 个服务、1 个 action 及 `ur_msgs` 的 21 个接口尚无本批类型化绑定。独立安装和线格式验收待完成。[固定版本的消息定义](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/tree/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg) · [上游注册清单](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/CMakeLists.txt)

## 按线顺序列出的字段

- `OperationalMode` 含 `string mode`，上游给出 `MANUAL` 与 `AUTOMATIC`。
- `ProgramInformation` 依次含 `string name`、`string description`、`uint64 created_date`、`uint64 last_saved_date`、`uint64 last_modified_date` 与 `string program_state`。三个日期字段保留仪表板返回的无符号值。上游给出 `DRAFT` 和 `FINAL` 两种修订状态。
- `ProgramState` 含 `string state`，上游给出 `STOPPED`、`PLAYING`、`PAUSED` 三种执行状态。
- `RobotMode` 含 `int8 mode`，10 个具名代码从 `NO_CONTROLLER`（−1）到 `UPDATING_FIRMWARE`（8）。
- `SafetyMode` 含 `uint8 mode`，上游为该无符号字段定义了 13 个具名代码。
- `SafetyStatus` 含 `int8 status`，上游为该有符号字段定义了 22 个具名代码。`IO_PLANE_STOP` 的值为 23，代码 21 在该版中未命名。
- `UserRole` 含 `string role`，上游给出 `PROGRAMMER`、`OPERATOR`、`NONE`、`LOCKED` 与 `RESTRICTED`。
- `VersionInformation` 依次含 `major`、`minor`、`bugfix`、`build`，四个字段均为 `uint32`。

每个公共类型保留 `ur_dashboard_msgs/msg/<Name>` 标识。驱动从仪表板应答复制三个日期和程序修订状态。编解码器保留上游未命名的代码和字符串。常量不占用报文字节。[仪表板应答映射](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_robot_driver/src/dashboard_client_ros.cpp#L377-L384)

## 报文与内存

传入含四字节封装头的完整 PLAIN_CDR 报文。头部依次为两字节表示标识和两字节选项。`00 00` 标识大端，`00 01` 标识小端。对齐从封装头后的第一个字节起算。字符串先写对齐后的 `uint32` 长度，该长度含末尾 NUL，空字符串的长度为 1。语言接口返回终止符之前的内容字节。

编码先计算完整长度，对齐字节和封装选项写零。解码核对每个字符串的长度、终止符及整个报文的长度。封装选项的低两位可声明传输层尾部填充数。填充数须与正文长度一致，解码器接受完整尾部或传输层已整体去除尾部的输入。其余封装选项和多余尾部数据会导致校验失败。

## C

包含 `<uwrosv2/universal_robots/cdr/ur_dashboard_msgs.h>`。记录名为 `uwrosv2_universal_robots_cdr_ur_dashboard_msgs_` 加 ROS 类型名，函数后缀为 `_defaults`、`_encoded_size`、`_encode`、`_decode`、`_validate`。记录名后加下划线及原常量名即可取得常量。字符串常量和解码后的字符串均为 `uwrosv2_universal_robots_cdr_string`，含 `data`、`size` 两个成员。

例如，`uwrosv2_universal_robots_cdr_ur_dashboard_msgs_RobotMode_decode(frame, length, &mode)` 成功后返回 1，写入 `mode.mode`。编码依次传入记录指针、`uwrosv2_universal_robots_cdr_big_endian` 或 `uwrosv2_universal_robots_cdr_little_endian`、输出地址、容量和写入字节数指针。解码失败时输出记录维持原值。编码的输入区域、输出区域和字节数槽应互不重叠。解码所得字符串借用的原报文须在使用期间保持可读且不可修改。

## C++98 及后续标准

包含 `<uwrosv2/universal_robots/cdr/ur_dashboard_msgs.hpp>`。可声明 `namespace cdr = uwrosv2::universal_robots::cdr`，用 `cdr::ur_dashboard_msgs::ProgramInformation::defaults()` 创建记录。调用 `cdr::encoded_size(value, size)`、`cdr::encode(value, cdr::big_endian, out, capacity, written)`、`cdr::decode(frame, size, value)` 或 `cdr::validate<T>(frame, size)`，均返回 `bool`。类型通过 `T::datatype()` 给出 ROS 名称。同级命名空间提供类型专属常量，例如 `cdr::ur_dashboard_msgs::ProgramInformation_Constants::PROGRAM_STATE_FINAL`。`cdr::string` 的借用及输出存储要求同 C。

## Rust

引入 `wros_observation::cdr::{Endian, Message}`，从 `wros_observation::cdr::ur_dashboard_msgs` 选择消息类型。使用 `T::default()`、`value.encoded_size()`、`value.encode(Endian::Little, &mut out)`、`T::decode(frame)` 与 `T::validate(frame)`。编解码操作返回 `Result`。`T::TYPE` 给出 ROS 名称，关联常量使用上游原名，例如 `ProgramState::PAUSED`。crate 使用 `no_std`，字符串字段为与输入报文生命周期绑定的 `&[u8]`。

## 可复制的工程

安装时选择 `--platform universal_robots` 和语言 `c`、`cpp` 或 `rust`。将所得 SDK 的整个 `examples/universal_robots/<语言>/cdr` 目录复制到新工程，设置 `UWVM_ROS_SDK_ROOT` 指向所选安装目录，即可使用 `xmake build` 和 `xmake test -j1`。三个工程均在来宾内存中转换手工构造的程序元数据报文，并比较两种端序的字节。原有 `observation` 接口和工程提供单独的 `SafetyStatus.status` 读取函数。
