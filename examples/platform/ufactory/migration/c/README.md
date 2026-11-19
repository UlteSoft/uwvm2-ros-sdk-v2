# ufactory · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `xarm_msgs` from the revision below to exercise `package://xarm_msgs/msg/IOState.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[3bc6c4da51769d90ce2a6d1419a0b65446d177e3](https://github.com/xArm-Developer/xarm_ros/tree/3bc6c4da51769d90ce2a6d1419a0b65446d177e3)
