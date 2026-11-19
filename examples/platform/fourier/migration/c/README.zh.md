# fourier · 有界厂商资源迁移

默认项目使用随 SDK 安装的 ROS 2 IMU 资源。要运行原厂 `config/config.yaml`，请将 `VENDOR_ROOT` 指向下列版本的本地厂商源码。SDK 为映射提供包清单，上游软件可以独立于 ROS。构建前执行以下命令。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

```sh
python3 "$UWVM_ROS_SDK_ROOT/examples/shared/migration/c/stage_vendor.py" \
  --project . --source-root "$VENDOR_ROOT" --output ./vendor-package
export WROS_ROS_PACKAGE_ROOT="$PWD/vendor-package"
xmake -j1
xmake test -j1
```

[b434869719ae256d02d8285e88ea2b22c1515602](https://github.com/FFTAI/fourier_aurora_sdk/tree/b434869719ae256d02d8285e88ea2b22c1515602)
