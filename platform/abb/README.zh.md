# ABB

C、C++、Rust 和 Go 可编解码 25 种 ABB ROS 1 消息、22 对服务请求与响应，以及公共的 Header。 [ROS1 消息与服务记录](ros1.zh.md)

选择 `--platform abb --language go` 安装 `wrgo`，选择 `--platform abb --language tinygo` 安装 `wrtg`。安装结果带有完整的 Go 模块和可复制的外部 Xmake 工程。英文指南按 EGM、RAPID、StateMachine 与 RWS 分域说明接口、字节布局和握手元数据。[ABB Go 模块与安装方法](../../include/u2rosv2/platform/abb/go/README.md)

选择 `--platform abb --language java` 安装原生 `wrjava` 工具链，外部工程可读取 EGM、RAPID、机器人控制器、StateMachine 状态和 GetRAPIDNum 服务正文。Java 安装和客户程序执行仍待独立验收。[Java 分域接口与外部构建](../../include/u2rosv2/platform/abb/java/README.md)

## 只读观测接口

`abb_rapid_msgs/Pos`。读取 RAPID pos 在 ROS 消息中的 X、Y、Z 三个分量。

输入为从第一个字段开始的 ROS 1 紧凑序列化消息正文。可读取的字段函数为 `read_x`、`read_y`、`read_z`。

C 包含 `<uwrosv2/abb/observation.h>`，函数带 `uwrosv2_abb_` 前缀。
C++98 及后续标准包含 `<uwrosv2/abb/observation.hpp>`，使用 `uwrosv2::abb` 命名空间。
C 函数接受输出指针，C++ 函数接受输出引用。解码成功时才写入输出。Rust 的 `wros_observation` crate 返回 `Option<T>`。
JS 和 TypeScript 从 `uwrosv2/platform/abb/observation` 导入函数，传入 `Uint8Array`。64 位整数返回 `bigint`，无效记录返回 `undefined`。
AssemblyScript 在有界驱动模式下读取请求暂存区，传入最后一个参数 true 可读取上一次成功回复。读取成功时返回 true，并更新同名字段值。
WAT 库 `include/u2rosv2/platform/abb/wat/observation.wat` 导出线性内存和上述函数。传入输入地址、长度、数组索引（如适用）和输出地址。成功返回 1，并将字段按原宽度以小端序写入。

## 在本地运行

安装时指定 `--platform abb` 和语言，将 `examples/abb/<language>` 复制到用户工程，设置 `UWVM_ROS_SDK_ROOT`、`WROS_VM`。
执行 `xmake build` 和 `xmake test -j1`。示例使用按原始定义构造的离线样本，校验字段值并拒绝截断数据。

## 上游定义

- [abb_rapid_msgs/msg/Pos.msg](https://github.com/ros-industrial/abb_robot_driver_interfaces/blob/da809cd0bb6f270c0814fca07d7d4a5c0385fc39/abb_rapid_msgs/msg/Pos.msg)

platform.json 记录各定义文件的 SHA-256 和源码版本。
