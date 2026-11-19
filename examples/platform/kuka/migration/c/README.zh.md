# kuka · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `kuka_driver_interfaces` 可改用 `package://kuka_driver_interfaces/msg/KssStatus.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[15fbb6941356390c38bbd135a0676dfd96a050c0](https://github.com/kuka-ros/kuka_drivers/tree/15fbb6941356390c38bbd135a0676dfd96a050c0)
