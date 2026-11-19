# nvidia-isaac-ros · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `isaac_ros_tensor_list_interfaces` 可改用 `package://isaac_ros_tensor_list_interfaces/msg/Tensor.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[7bec6ae5dbb2faa11617f40226e8932a4a94e6e4](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common/tree/7bec6ae5dbb2faa11617f40226e8932a4a94e6e4)
