# ubtech · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `src/grab_demo_msgs` 可改用 `package://grab_demo_msgs/msg/IKRequest.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[3df9f9dc7689203fb673a21d8205bb597ed4fafe](https://github.com/UBTECH-Robot/tk_sdk_demo/tree/3df9f9dc7689203fb673a21d8205bb597ed4fafe)
