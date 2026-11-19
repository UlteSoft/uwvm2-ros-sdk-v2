# kinova · C resource migration

The offline build embeds the pinned ROS 2 IMU definition. Set `WROS_ROS_PACKAGE_ROOT` to `kortex_description` from the revision below to exercise `package://kortex_description/arms/gen3/6dof/config/joint_limits.yaml`. The host verifies both hashes in `upstream.lock`. [Build and test](../../../../../document/en/platform-migration-examples.md).

[b2aa46b29ae8fadd5b293c57e3500925c61eb8e8](https://github.com/Kinovarobotics/ros2_kortex/tree/b2aa46b29ae8fadd5b293c57e3500925c61eb8e8)
