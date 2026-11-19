# hello_robot · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `stretch_calibration` from the revision below to exercise `package://stretch_calibration/config/head_calibration_options.yaml`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[751e701b87d6f34dd26df1c4abc39229d68e60ff](https://github.com/hello-robot/stretch_ros2/tree/751e701b87d6f34dd26df1c4abc39229d68e60ff)
