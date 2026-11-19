# elephant · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `myArm/myarm_communication` 可改用 `package://myarm_communication/msg/MyArmPumpStatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[3a0357d2afec2706c299f6d51ac46b6b128067f8](https://github.com/elephantrobotics/mycobot_ros/tree/3a0357d2afec2706c299f6d51ac46b6b128067f8)
