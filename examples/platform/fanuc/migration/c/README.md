# fanuc · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `fanuc_msgs` from the revision below to exercise `package://fanuc_msgs/msg/RMIStatus.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[da5db3f611cdc9dffe687e056c4e79bea584bf5c](https://github.com/FANUC-CORPORATION/fanuc_driver/tree/da5db3f611cdc9dffe687e056c4e79bea584bf5c)
