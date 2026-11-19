# nvidia-isaac-sim · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `source/extensions/isaacsim.asset.importer.urdf/data/urdf/robots/franka_description` 可改用 `package://franka_description/robots/panda_arm.urdf`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[87c95274f50836068b44eeb030bf62aa2108bdf8](https://github.com/isaac-sim/IsaacSim/tree/87c95274f50836068b44eeb030bf62aa2108bdf8)
