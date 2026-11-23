# boston_dynamics 只读观测

`bosdyn.api.PointCloud.data`。读取 Spot 点云的 XYZ_32F 数据字段。每个点包含三个连续的小端 float32。传入已提取的 protobuf 字节字段和从零开始的点索引。

输入为上述字段或记录的小端字节序列。可读取的字段函数为 `read_x`、`read_y`、`read_z`。

C 包含 `<uwrosv2/boston_dynamics/observation.h>`，函数带 `uwrosv2_boston_dynamics_` 前缀。
C++98 及后续标准包含 `<uwrosv2/boston_dynamics/observation.hpp>`，使用 `uwrosv2::boston_dynamics` 命名空间。
C 函数接受输出指针，C++ 函数接受输出引用。解码成功时才写入输出。Rust 的 `wros_observation` crate 返回 `Option<T>`。
JS 和 TypeScript 从 `uwrosv2/platform/boston_dynamics/observation` 导入函数，传入 `Uint8Array`。64 位整数返回 `bigint`，无效记录返回 `undefined`。
AssemblyScript 在有界驱动模式下读取请求暂存区，传入最后一个参数 true 可读取上一次成功回复。读取成功时返回 true，并更新同名字段值。
WAT 库 `include/u2rosv2/platform/boston_dynamics/wat/observation.wat` 导出线性内存和上述函数。传入输入地址、长度、数组索引（如适用）和输出地址。成功返回 1，并将字段按原宽度以小端序写入。

## 在本地运行

安装时指定 `--platform boston_dynamics` 和语言，将 `examples/boston_dynamics/<language>` 复制到用户工程，设置 `UWVM_ROS_SDK_ROOT`、`WROS_VM`。
执行 `xmake build` 和 `xmake test -j1`。示例使用按原始定义构造的离线样本，校验字段值并拒绝截断数据。

## 上游定义

- [protos/bosdyn/api/point_cloud.proto](https://github.com/boston-dynamics/spot-sdk/blob/16a98aae3b818082288504c6e53b59a67666aaeb/protos/bosdyn/api/point_cloud.proto)

platform.json 记录各定义文件的 SHA-256 和源码版本。
