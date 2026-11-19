# ufactory · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `xarm_msgs` 可改用 `package://xarm_msgs/msg/IOState.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[3bc6c4da51769d90ce2a6d1419a0b65446d177e3](https://github.com/xArm-Developer/xarm_ros/tree/3bc6c4da51769d90ce2a6d1419a0b65446d177e3)
