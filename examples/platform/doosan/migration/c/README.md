# doosan · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `robot_ws/src/dsr_msgs` from the revision below to exercise `package://dsr_msgs/msg/LogAlarm.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[19d520d7df599dc9751f3e8a41337c399c418a47](https://github.com/DoosanRobotics/doosan-robot/tree/19d520d7df599dc9751f3e8a41337c399c418a47)
