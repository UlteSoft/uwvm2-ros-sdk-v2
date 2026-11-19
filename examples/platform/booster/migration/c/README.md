# booster · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `src/interface/booster_ros2_interface` from the revision below to exercise `package://booster_interface/msg/ImuState.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[fa4f31ccb4428a9e60e90b4f54eb80499caeb0ca](https://github.com/BoosterRobotics/robocup_demo/tree/fa4f31ccb4428a9e60e90b4f54eb80499caeb0ca)
