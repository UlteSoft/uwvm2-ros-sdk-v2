# franka · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `franka_msgs` 可改用 `package://franka_msgs/msg/Elbow.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec](https://github.com/frankarobotics/franka_ros2/tree/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec)
