# agilex · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `scout_msgs` 可改用 `package://scout_msgs/msg/ScoutStatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[01e07881cdc566c3a657e288c59a75577992d13e](https://github.com/agilexrobotics/scout_ros/tree/01e07881cdc566c3a657e288c59a75577992d13e)
