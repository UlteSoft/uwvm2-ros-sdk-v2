# trossen · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `interbotix_ros_xseries/interbotix_xs_msgs` from the revision below to exercise `package://interbotix_xs_msgs/msg/ArmJoy.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[172841ffa93f7556fff9c7455ad0e77688fa156e](https://github.com/Interbotix/interbotix_ros_core/tree/172841ffa93f7556fff9c7455ad0e77688fa156e)
