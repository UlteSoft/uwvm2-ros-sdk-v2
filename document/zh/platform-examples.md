# 构建与测试平台示例

在 examples/platform 下依次选择平台、示例类别、语言。每个叶目录都包含可独立构建的 xmake 工程和可编辑的客户程序源码。例如 examples/platform/unitree/common/c 会生成两个可分别运行的 Wasm：common 模块检查 ROS ABI，sensor 模块用重复测量和异常值检查中值滤波。两个目标都登记了解释器和 AOT 测试。

~~~sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree \
  --language c --site-profile "$C_SITE" --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT="$PWD/sdk/$SDK_COMMIT/unitree/c/development"
export WROS_VM=/absolute/path/to/uwvm2-ros
cp -r "$UWVM_ROS_SDK_ROOT/examples/platform/unitree/common/c" ./samples
cd samples
xmake f -p wasm-wasip1 -a wasm32 -y
xmake build
xmake test -j1
~~~

安装位置以安装器输出的 directory 为准。各语言需要的工具链站点和编译配置见对应语言指南。按提交安装时只会下载所选平台和语言的示例。在工程目录中运行 xmake build 可生成该工程的所有 Wasm，也可指定单个目标。产物位于 build 目录。xmake test -j1 会启动独立 VM 执行每组断言；导入被隐藏、VM 报错或程序触发陷阱都会使测试失败。示例只声明本地测试需要的查询许可，现场部署另行审阅授权。

| 子目录 | 工程验证的内容 |
| --- | --- |
| common | 可移植的计算或 ROSv2 调用，例如读取 ABI、处理测距数据。 |
| extension | 经过公共认证驱动通道验证当前平台的子权限。 |
| migration | 移植一个有明确来源的旧 ROS 行为或资源约定。 |

## 驱动权限示例

Linux 测试程序建立私有 SOCK_SEQPACKET 套接字对，准备一次性密封的 Ed25519 身份和测试会话。客户程序打开分配给自己的 arm 能力并请求 driver.connect。第一种配置给父资源连接权、关闭平台子权限。第二种打开子权限、只给父资源断连权。两次都必须收到 EACCES，且对端收到零字节。测试结束时还会检查会话仍在有效期内。夹具使用 Python 3 和 cryptography，完全不接入执行器。厂商协议、物理仿真和硬件停机需要另外验证。

## 源码迁移示例

栅格索引示例移植了 Noetic Costmap2D 的无符号行优先坐标换算，并在 VM 中校验已知坐标的实际索引。工程源码注明了算法以及输入范围。其他迁移工程分别采用有名称的 ROS 消息和资源夹具。[ROS Noetic Costmap2D 源码](https://github.com/ros-planning/navigation/blob/noetic-devel/costmap_2d/include/costmap_2d/costmap_2d.h)

## 源码接口文档

从完整源码仓库执行 doxygen document/source/Doxyfile。C 接口参考文档逐项列出 share/abi/ros.json 中的操作、线格式、请求与返回字段顺序、适用的资源用途、地址参数和返回值含义。生成的 HTML 位于 .tmp/doxygen/html。[ROSv2 源码参考](../source/ros-abi.dox) · [xmake 参数](xmake.md)
