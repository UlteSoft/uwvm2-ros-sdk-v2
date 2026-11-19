# flexiv · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `flexiv_msgs` 可改用 `package://flexiv_msgs/msg/OperationalStatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[5188d2a4473e556a88ee0cfbe858e84ddd6979b8](https://github.com/flexivrobotics/flexiv_ros2/tree/5188d2a4473e556a88ee0cfbe858e84ddd6979b8)
