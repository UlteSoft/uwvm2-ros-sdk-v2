# nvidia-groot · Bounded vendor resource migration

The default project uses the bundled ROS 2 IMU fixture. To test the original `demo_data/droid_sample/meta/modality.json`, point `VENDOR_ROOT` to a local copy of the pinned GR00T N1.7 release. This example supplies a ROS package manifest to map the dataset metadata into a package resource. [Build and test](../../../../../document/en/platform-migration-examples.md).

```sh
python3 "$UWVM_ROS_SDK_ROOT/examples/shared/migration/c/stage_vendor.py" \
  --project . --source-root "$VENDOR_ROOT" --output ./vendor-package
export WROS_ROS_PACKAGE_ROOT="$PWD/vendor-package"
xmake -j1
xmake test -j1
```

The DROID resource test covers data migration. NVIDIA publishes a separate GR00T deployment workflow for the Unitree G1. That workflow provides a MuJoCo launch with a LEAPP policy and ROS 2 Control. The packaged MuJoCo scene serves as a launch smoke test because it contains no manipulation objects. [Pinned GR00T N1.7 source](https://github.com/NVIDIA/Isaac-GR00T/tree/23ace64f17aa5015259b8609d371eb61a357c776), [Isaac ROS 5.1 Unitree G1 workflow](https://nvidia-isaac-ros.github.io/v/release-5.1/repositories_and_packages/isaac_ros_physical_ai/isaac_ros_unitree_g1_gr00t/index.html).
