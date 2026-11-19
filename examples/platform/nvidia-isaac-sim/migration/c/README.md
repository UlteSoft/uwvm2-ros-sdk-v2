# nvidia-isaac-sim · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `source/extensions/isaacsim.asset.importer.urdf/data/urdf/robots/franka_description` from the revision below to exercise `package://franka_description/robots/panda_arm.urdf`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[87c95274f50836068b44eeb030bf62aa2108bdf8](https://github.com/isaac-sim/IsaacSim/tree/87c95274f50836068b44eeb030bf62aa2108bdf8)
