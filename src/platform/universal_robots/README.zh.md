# Universal Robots 接口源码

[English](README.md)

ROS 2 Driver 7.3.0 的 Jazzy 依赖清单选用 ROS-Industrial 的 humble-devel 消息包，SDK 固定到该包的 2.7.0 发行。审阅目录包含两个上游 CMake 文件注册的全部接口声明。清单给出官方地址、tag、完整提交、许可证，以及逐文件的 Git blob 和 SHA-256。[官方驱动依赖](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/Universal_Robots_ROS2_Driver.jazzy.repos) · [源码清单](upstream.json)

- `ur_dashboard_msgs` 有 8 种消息、25 个服务和 1 个 action。上游 dashboard ROS 节点实际使用机器人模式和程序状态查询。[上游接口声明](upstream/ur_dashboard_msgs/CMakeLists.txt) · [驱动调用点](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_robot_driver/src/dashboard_client_ros.cpp)
- `ur_msgs` 有 10 种消息、8 个服务和 3 个 action。上游 GPIO 控制器实际发布 IOStates 和 ToolDataMsg。[上游接口声明](upstream/ur_msgs/CMakeLists.txt) · [控制器发布点](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_controllers/src/gpio_controller.cpp#L279)

C、C++ 和 Rust 的仪表板接口提供 8 种消息、16 个字段、57 个具名常量，以及带封装头的大小端 XCDRv1 编解码器。另外四种观测绑定提供原有的 SafetyStatus 字段读取。其余 47 个上游接口包括 10 种消息、33 个服务和 4 个 action。独立安装、互操作及运行验收待完成。[公共仪表板接口](../../../platform/universal_robots/cdr.zh.md) · [观测接口](../../../platform/universal_robots/README.zh.md)

在 SDK 仓库根目录运行 `python3 -B src/platform/universal_robots/generate_cdr.py`，可重新生成本平台的仪表板类型、标量编解码器、许可说明、示例字节，以及观测接口的模块注册。生成器读取上游登记的仪表板消息路径，按固定清单核对 SHA-256，并在生成时复用既有的原生 XCDRv1 字节与 C 报文封装模板。每个语言安装包自带完整编解码器。[生成器](generate_cdr.py) · [手工构造的 ProgramInformation 样本](program_information_frames.json)
