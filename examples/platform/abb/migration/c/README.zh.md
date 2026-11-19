# abb · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `abb_rapid_msgs` 可改用 `package://abb_rapid_msgs/msg/Pos.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[da809cd0bb6f270c0814fca07d7d4a5c0385fc39](https://github.com/ros-industrial/abb_robot_driver_interfaces/tree/da809cd0bb6f270c0814fca07d7d4a5c0385fc39)
