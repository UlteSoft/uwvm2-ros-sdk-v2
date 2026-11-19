# deep_robotics · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `src/drdds` 可改用 `package://drdds/msg/ImuData.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[9ea6ee94bfe90c9a36f5799d39f8dc1d821128db](https://github.com/DeepRoboticsLab/sdk_deploy/tree/9ea6ee94bfe90c9a36f5799d39f8dc1d821128db)
