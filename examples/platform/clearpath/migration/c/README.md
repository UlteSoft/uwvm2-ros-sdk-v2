# clearpath · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `clearpath_outdoornav_msgs/clearpath_safety_msgs` from the revision below to exercise `package://clearpath_safety_msgs/msg/WatchdogConfigNodeStatus.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[c17b52e7ba7061310493b43d5b1cd4ffd33cc9b6](https://github.com/clearpathrobotics/clearpath_msgs/tree/c17b52e7ba7061310493b43d5b1cd4ffd33cc9b6)
