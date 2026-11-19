# dobot · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `dobot_msgs_v4` from the revision below to exercise `package://dobot_msgs_v4/msg/RobotStatus.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[ec201c40d5db63185a3593ec9c39f80fe25aa527](https://github.com/Dobot-Arm/DOBOT_6Axis_ROS2_V4/tree/ec201c40d5db63185a3593ec9c39f80fe25aa527)
