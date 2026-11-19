# dobot · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `dobot_msgs_v4` 可改用 `package://dobot_msgs_v4/msg/RobotStatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[ec201c40d5db63185a3593ec9c39f80fe25aa527](https://github.com/Dobot-Arm/DOBOT_6Axis_ROS2_V4/tree/ec201c40d5db63185a3593ec9c39f80fe25aa527)
