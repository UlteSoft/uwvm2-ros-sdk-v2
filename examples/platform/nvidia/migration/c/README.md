# nvidia · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `isaac_ros_tensor_list_interfaces` from the revision below to exercise `package://isaac_ros_tensor_list_interfaces/msg/Tensor.msg`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[7bec6ae5dbb2faa11617f40226e8932a4a94e6e4](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common/tree/7bec6ae5dbb2faa11617f40226e8932a4a94e6e4)
