# kuka · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `kuka_driver_interfaces` from the revision below to exercise `package://kuka_driver_interfaces/msg/KssStatus.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[15fbb6941356390c38bbd135a0676dfd96a050c0](https://github.com/kuka-ros/kuka_drivers/tree/15fbb6941356390c38bbd135a0676dfd96a050c0)
