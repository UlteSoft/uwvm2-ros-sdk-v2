# realman · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `rm_ros_interfaces` from the revision below to exercise `package://rm_ros_interfaces/msg/Armcurrentstatus.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[5fc226e93358e73c165b2af54b583389f813049e](https://github.com/RealManRobot/ros2_rm_robot/tree/5fc226e93358e73c165b2af54b583389f813049e)
