# robotis · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `.` 可改用 `package://turtlebot3_msgs/msg/SensorState.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[76e78b0a34e07cf1dd16dafdc54c44f35c5b83eb](https://github.com/ROBOTIS-GIT/turtlebot3_msgs/tree/76e78b0a34e07cf1dd16dafdc54c44f35c5b83eb)
