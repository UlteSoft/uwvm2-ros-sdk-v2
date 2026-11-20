# nvidia-isaac-ros · C 资源迁移

离线构建会嵌入固定版本的 ROS 2 IMU 定义。使用 NVIDIA 张量定义时，将 `WROS_ROS_PACKAGE_ROOT` 指向本地的 `isaac_ros_tensor_list_interfaces` 包。Xmake 默认选用 5.0.0 的锁文件。使用 5.1.0 时，先执行 `xmake f -c -y -a wasm32 --isaac_ros_release=5.1`，再构建和测试。宿主根据所选锁文件核对 `Tensor.msg` 与 `package.xml` 的摘要，然后嵌入资源。[构建与测试](../../../../../document/zh/platform-migration-examples.md)。

Wasm 测试在模块内存中检查已嵌入的资源。DDS 互通、`rosidl::Buffer` CUDA 传输以及 TensorRT 或 Triton 运行需要独立的运行时测试。[Isaac ROS 5.0.0 源码](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common/tree/7bec6ae5dbb2faa11617f40226e8932a4a94e6e4)、[Isaac ROS 5.1.0 源码](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common/tree/57a6485a1322e38791b1cb21c20a9e897fbc50a5)、[Isaac ROS 5.1 文档](https://nvidia-isaac-ros.github.io/v/release-5.1/repositories_and_packages/isaac_ros_dnn_inference/index.html)。
