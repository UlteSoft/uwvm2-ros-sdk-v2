# hello_robot 只读观测

`Wacc_Protocol_P0.unpack_status`。读取 Stretch 腕部加速度计在小端主机上的 P0 状态正文，输入从 RPC 标识或可选扩展之后开始。时间戳为主机转换前的设备计数。

输入为上述字段或记录的小端字节序列。可读取的字段函数为 `read_ax`、`read_az`、`read_a0`、`read_single_tap_count`、`read_timestamp`。

C 包含 `<uwrosv2/hello_robot/observation.h>`，函数带 `uwrosv2_hello_robot_` 前缀。
C++98 及后续标准包含 `<uwrosv2/hello_robot/observation.hpp>`，使用 `uwrosv2::hello_robot` 命名空间。
C 函数接受输出指针，C++ 函数接受输出引用。解码成功时才写入输出。Rust 的 `wros_observation` crate 返回 `Option<T>`。
JS 和 TypeScript 从 `uwrosv2/platform/hello_robot/observation` 导入函数，传入 `Uint8Array`。64 位整数返回 `bigint`，无效记录返回 `undefined`。
AssemblyScript 在有界驱动模式下读取请求暂存区，传入最后一个参数 true 可读取上一次成功回复。读取成功时返回 true，并更新同名字段值。
WAT 库 `include/u2rosv2/platform/hello_robot/wat/observation.wat` 导出线性内存和上述函数。传入输入地址、长度、数组索引（如适用）和输出地址。成功返回 1，并将字段按原宽度以小端序写入。

## 在本地运行

安装时指定 `--platform hello_robot` 和语言，将 `examples/hello_robot/<language>` 复制到用户工程，设置 `UWVM_ROS_SDK_ROOT`、`WROS_VM`。
执行 `xmake build` 和 `xmake test -j1`。示例使用按原始定义构造的离线样本，校验字段值并拒绝截断数据。

## 上游定义

- [body/stretch_body/wacc.py](https://github.com/hello-robot/stretch_body/blob/92c9db0cc9ade6535f822e83bbf10cbd0c68136a/body/stretch_body/wacc.py)
- [body/stretch_body/transport.py](https://github.com/hello-robot/stretch_body/blob/92c9db0cc9ade6535f822e83bbf10cbd0c68136a/body/stretch_body/transport.py)

platform.json 记录各定义文件的 SHA-256 和源码版本。
