# pal · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `pal_walking_msgs` 可改用 `package://pal_walking_msgs/msg/SMStatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[a9b3d52908626e0cf1f230b4dc4a962299d232f3](https://github.com/pal-robotics/pal_msgs/tree/a9b3d52908626e0cf1f230b4dc4a962299d232f3)
