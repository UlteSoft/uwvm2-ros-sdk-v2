# unitree · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `cyclonedds_ws/src/unitree/unitree_go` from the revision below to exercise `package://unitree_go/msg/IMUState.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[668d1ec5a05d1c38d3306bdca7d59f2ba3581a88](https://github.com/unitreerobotics/unitree_ros2/tree/668d1ec5a05d1c38d3306bdca7d59f2ba3581a88)
