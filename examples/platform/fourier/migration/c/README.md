# fourier · Bounded vendor resource migration

The default project uses the bundled ROS 2 IMU fixture. To use the original `config/config.yaml`, point `VENDOR_ROOT` to the locally supplied vendor repository at the pinned revision. This project supplies a ROS package manifest for this mapping. The original upstream software need not be a ROS package. Run these commands before building. [Build and test](../../../../../document/en/platform-migration-examples.md).

```sh
python3 "$UWVM_ROS_SDK_ROOT/examples/shared/migration/c/stage_vendor.py" \
  --project . --source-root "$VENDOR_ROOT" --output ./vendor-package
export WROS_ROS_PACKAGE_ROOT="$PWD/vendor-package"
xmake -j1
xmake test -j1
```

[b434869719ae256d02d8285e88ea2b22c1515602](https://github.com/FFTAI/fourier_aurora_sdk/tree/b434869719ae256d02d8285e88ea2b22c1515602)
