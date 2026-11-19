# doosan · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `robot_ws/src/dsr_msgs` 可改用 `package://dsr_msgs/msg/LogAlarm.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[19d520d7df599dc9751f3e8a41337c399c418a47](https://github.com/DoosanRobotics/doosan-robot/tree/19d520d7df599dc9751f3e8a41337c399c418a47)
