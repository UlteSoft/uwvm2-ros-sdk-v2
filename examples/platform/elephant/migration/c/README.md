# elephant · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `myArm/myarm_communication` from the revision below to exercise `package://myarm_communication/msg/MyArmPumpStatus.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[3a0357d2afec2706c299f6d51ac46b6b128067f8](https://github.com/elephantrobotics/mycobot_ros/tree/3a0357d2afec2706c299f6d51ac46b6b128067f8)
