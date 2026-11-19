# agibot · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `src/aimdk_msgs/prebuilt_aarch64/share/aimdk_msgs` from the revision below to exercise `package://aimdk_msgs/msg/JointState.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[5bbcf724d54fb28f153db0d272f9acb7906bb1d2cac7dd7ccdc699a5c7eeab35](https://x2-aimdk.agibot.com/downloads/aimdk-sdk-v1_0_0-aimdk-aarch64-a424add7-artifacts.zip)
