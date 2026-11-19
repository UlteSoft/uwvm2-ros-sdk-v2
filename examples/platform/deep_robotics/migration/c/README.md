# deep_robotics · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `src/drdds` from the revision below to exercise `package://drdds/msg/ImuData.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[9ea6ee94bfe90c9a36f5799d39f8dc1d821128db](https://github.com/DeepRoboticsLab/sdk_deploy/tree/9ea6ee94bfe90c9a36f5799d39f8dc1d821128db)
