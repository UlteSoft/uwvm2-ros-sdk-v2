# universal_robots · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `ur_dashboard_msgs` from the revision below to exercise `package://ur_dashboard_msgs/msg/SafetyStatus.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[262330ed9b5467a17c8ceae09567991e22d13944](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/tree/262330ed9b5467a17c8ceae09567991e22d13944)
