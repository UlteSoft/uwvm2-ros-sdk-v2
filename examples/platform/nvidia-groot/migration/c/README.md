# nvidia-groot · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `sensor_msgs` from the revision below to exercise `package://sensor_msgs/msg/Imu.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[a941f14bb318d8d904505ed935ccbb97f24a70a4](https://github.com/ros2/common_interfaces/tree/a941f14bb318d8d904505ed935ccbb97f24a70a4)
