# booster · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `src/interface/booster_ros2_interface` 可改用 `package://booster_interface/msg/ImuState.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[fa4f31ccb4428a9e60e90b4f54eb80499caeb0ca](https://github.com/BoosterRobotics/robocup_demo/tree/fa4f31ccb4428a9e60e90b4f54eb80499caeb0ca)
