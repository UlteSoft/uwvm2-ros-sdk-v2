# agilex · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `scout_msgs` from the revision below to exercise `package://scout_msgs/msg/ScoutStatus.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[01e07881cdc566c3a657e288c59a75577992d13e](https://github.com/agilexrobotics/scout_ros/tree/01e07881cdc566c3a657e288c59a75577992d13e)
