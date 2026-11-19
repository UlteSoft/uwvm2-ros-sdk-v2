# abb · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `abb_rapid_msgs` from the revision below to exercise `package://abb_rapid_msgs/msg/Pos.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[da809cd0bb6f270c0814fca07d7d4a5c0385fc39](https://github.com/ros-industrial/abb_robot_driver_interfaces/tree/da809cd0bb6f270c0814fca07d7d4a5c0385fc39)
