# fanuc · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `fanuc_msgs` 可改用 `package://fanuc_msgs/msg/RMIStatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[da5db3f611cdc9dffe687e056c4e79bea584bf5c](https://github.com/FANUC-CORPORATION/fanuc_driver/tree/da5db3f611cdc9dffe687e056c4e79bea584bf5c)
