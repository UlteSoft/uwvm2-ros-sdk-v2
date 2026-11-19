# nvidia-groot · Bounded vendor resource migration

The default project uses the bundled ROS 2 IMU fixture. To use the original `demo_data/droid_sample/meta/modality.json`, point `VENDOR_ROOT` to the locally supplied vendor repository at the pinned revision. This project supplies a ROS package manifest for this mapping. The original upstream software need not be a ROS package. Run these commands before building. [Build and test](../../../../../document/en/platform-migration-examples.md).

```sh
python3 "$UWVM_ROS_SDK_ROOT/examples/shared/migration/c/stage_vendor.py" \
  --project . --source-root "$VENDOR_ROOT" --output ./vendor-package
export WROS_ROS_PACKAGE_ROOT="$PWD/vendor-package"
xmake -j1
xmake test -j1
```

[dac54b313160c201c450f97df0fd74ebd379c892](https://github.com/NVIDIA/Isaac-GR00T/tree/dac54b313160c201c450f97df0fd74ebd379c892)
