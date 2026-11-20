# nvidia-groot · 有界厂商资源迁移

默认项目使用随 SDK 安装的 ROS 2 IMU 资源。要测试原厂 `demo_data/droid_sample/meta/modality.json`，请将 `VENDOR_ROOT` 指向固定版本的本地 GR00T N1.7 源码。此示例提供 ROS 包清单，将数据集元数据映射为软件包资源。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

```sh
python3 "$UWVM_ROS_SDK_ROOT/examples/shared/migration/c/stage_vendor.py" \
  --project . --source-root "$VENDOR_ROOT" --output ./vendor-package
export WROS_ROS_PACKAGE_ROOT="$PWD/vendor-package"
xmake -j1
xmake test -j1
```

本例通过 DROID 资源测试数据迁移。NVIDIA 另行发布了 Unitree G1 的 GR00T 部署流程，其 MuJoCo 启动入口使用 LEAPP 策略和 ROS 2 Control。配套 MuJoCo 场景没有操作对象，可用于验证应用启动。[固定版本的 GR00T N1.7 源码](https://github.com/NVIDIA/Isaac-GR00T/tree/23ace64f17aa5015259b8609d371eb61a357c776)、[Isaac ROS 5.1 Unitree G1 流程](https://nvidia-isaac-ros.github.io/v/release-5.1/repositories_and_packages/isaac_ros_physical_ai/isaac_ros_unitree_g1_gr00t/index.html)。
