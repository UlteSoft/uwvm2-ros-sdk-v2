# 平台绑定如何验收

每个子任务只负责一个具名平台。开发使用 GPT-6.2 Astra、max 推理和默认速度。开发者冻结提交并结束后，主线程把相同源码的 GitHub 候选提交交给新启动的 GPT-6.2 Sol，用 max 推理和默认速度独立验收。Sol 写下结果并结束后，新的 Astra 接手该平台的修复。一次通过的结果只覆盖记录中的上游版本、语言、编译器配置和实际运行过的接口。

对每个平台列出原厂发布的库、协议、驱动和上游示例，保存上游 URL、版本和完整提交。分别标出原厂接口、驱动公开接口以及社区移植。按实际公共符号和注册代码核对命名空间、类型、常量、单位、字段顺序、服务请求与应答、动作阶段、错误、版本差异和所需的授权。Wasm 应用通过 VM 授予的能力访问驱动。与控制器建立连接、认证和设备生命周期由宿主端负责。

每种目标语言都需要同一套有类型的公共接口、语言原生文档和可复制的外部 Xmake 工程。完整性核对覆盖通用语言清单的每个选择。语言别名和互操作桥单独列出。缺少编译器、解释器或运行时的语言保留缺失原因。记录区分源码、实际 Wasm 编译、独立上游格式比对、INT/AOT 运行和厂商仿真。

安装验收从 GitHub 的根安装器开始，使用指定提交、空 HOME 和空缓存。下载后的编译和运行在断网的 namespace 中执行。测试进程与协调进程分离，父 cgroup 和测试子组均限制为 64 GiB、零 swap。外部项目应分别用安装的命令和 Xmake 运行。每个结果保留源修订、模块摘要、运行配置和断言。取一个字段的示例只覆盖该字段及实际执行的路径。

每个厂商的每种语言都单独从 GitHub 下载安装器和选定工具链，再由外部工程开发、编译、运行。只有该厂商的全部目标语言都走通这条路径，才能把该厂商记为通过。

## ABB 的第一个上游基线

ROS 1 的四个 ABB 接口包有 25 个消息定义和 22 个服务定义。每项服务都有请求和应答。ABB 的 RAPID 数据、EGM 反馈、系统状态以及状态机设置属于不同接口。额外的 ROS 标准消息、服务或动作按所属库单列。RobotWare 版本、StateMachine Add-In 和控制器选项也会改变驱动实际注册的服务。ROS 2 接口来自独立的社区移植，编解码要对照相应的 CDR 实现单独验收。[ROS 1 定义](../../src/platform/abb/upstream/ros1/) · [ROS 2 定义](../../src/platform/abb/upstream/ros2/) · [驱动注册源码](../../src/platform/abb/upstream/abb_robot_driver/)

EGM 原生协议、RWS 客户端和 EGM/RWS 管理库分别有固定版本。EGM 的原厂 protobuf 消息和库自己的包装消息分别保留。ROS 消息通过验收时，只更新相应 ROS 接口的结果。ABB 在 RobotWare 7 与 8 的 RWS 文档以及 PC SDK 等产品公开的接口有各自的版本和运行环境，其覆盖仍待逐项实现和验收。[EGM 协议来源](../../src/platform/abb/upstream/abb_libegm/proto/README.md) · [RWS 库](../../src/platform/abb/upstream/abb_librws/) · [EGM/RWS 管理库](../../src/platform/abb/upstream/abb_egm_rws_managers/) · [ABB RWS 版本](https://robotwebservices.robotics.abb.com/) · [ABB Developer Center](https://developercenter.robotstudio.com/)
