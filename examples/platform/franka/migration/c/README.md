# franka · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `franka_msgs` from the revision below to exercise `package://franka_msgs/msg/Elbow.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec](https://github.com/frankarobotics/franka_ros2/tree/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec)
