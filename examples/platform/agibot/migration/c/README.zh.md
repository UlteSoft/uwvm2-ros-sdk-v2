# agibot · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。将 `WROS_ROS_PACKAGE_ROOT` 指向下列版本的 `src/aimdk_msgs/prebuilt_aarch64/share/aimdk_msgs` 可改用 `package://aimdk_msgs/msg/JointState.msg`。宿主将核对 `upstream.lock` 中的资源与清单摘要。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

[5bbcf724d54fb28f153db0d272f9acb7906bb1d2cac7dd7ccdc699a5c7eeab35](https://x2-aimdk.agibot.com/downloads/aimdk-sdk-v1_0_0-aimdk-aarch64-a424add7-artifacts.zip)
