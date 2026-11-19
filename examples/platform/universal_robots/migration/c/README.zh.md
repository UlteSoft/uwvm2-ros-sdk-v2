# universal_robots · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `ur_dashboard_msgs` 可改用 `package://ur_dashboard_msgs/msg/SafetyStatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[262330ed9b5467a17c8ceae09567991e22d13944](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/tree/262330ed9b5467a17c8ceae09567991e22d13944)
