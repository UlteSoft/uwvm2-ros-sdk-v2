# trossen · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `interbotix_ros_xseries/interbotix_xs_msgs` 可改用 `package://interbotix_xs_msgs/msg/ArmJoy.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[172841ffa93f7556fff9c7455ad0e77688fa156e](https://github.com/Interbotix/interbotix_ros_core/tree/172841ffa93f7556fff9c7455ad0e77688fa156e)
