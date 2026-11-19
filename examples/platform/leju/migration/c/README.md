# leju · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `src/leju_mobile_base_msgs` from the revision below to exercise `package://leju_mobile_base_msgs/msg/Battery.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[2634d9fa891bb9b4987cddc7977599922342a316](https://github.com/LejuRobotics/kuavo-ros-opensource/tree/2634d9fa891bb9b4987cddc7977599922342a316)
