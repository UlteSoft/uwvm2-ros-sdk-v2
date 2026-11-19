# realman · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `rm_ros_interfaces` 可改用 `package://rm_ros_interfaces/msg/Armcurrentstatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[5fc226e93358e73c165b2af54b583389f813049e](https://github.com/RealManRobot/ros2_rm_robot/tree/5fc226e93358e73c165b2af54b583389f813049e)
