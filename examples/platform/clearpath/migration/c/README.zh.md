# clearpath · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `clearpath_outdoornav_msgs/clearpath_safety_msgs` 可改用 `package://clearpath_safety_msgs/msg/WatchdogConfigNodeStatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[c17b52e7ba7061310493b43d5b1cd4ffd33cc9b6](https://github.com/clearpathrobotics/clearpath_msgs/tree/c17b52e7ba7061310493b43d5b1cd4ffd33cc9b6)
