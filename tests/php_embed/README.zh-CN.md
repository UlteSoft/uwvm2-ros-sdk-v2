# PHP 8.6 Embed SAPI 验证

此测试用 SDK 验证过的 C 编译器和配套 sysroot，将 PHP 8.6.0 官方 Zend 引擎及
静态 Embed SAPI 构建为 Core Wasm。在 UWVM2 解释器和 AOT 引擎中执行同一模块，
验证 PHP 数组遍历、算术、异常、输出捕获、宿主文件及环境变量访问拒绝。
另用 C 控制用例验证 Zend bailout 所依赖的 setjmp/longjmp 运行时。

使用现有的 64 GiB cgroup 门控。选择 `.tmp` 下的新输出目录，按英文版文档中的
命令传入 PHP 发布归档、wasi-libc SDK 34 源码归档、SDK 工具链、精确匹配的
sysroot 构建清单和 UWVM2 可执行文件。

默认目标为 wasm32 Core 3.0，支持标准 Wasm 异常并启用 SDK 的相邻分配标签管理。
测试检查实际解码出的所有权指令，并分别启用和关闭运行时标签校验。显式传入
`--no-mte` 可无标签构建，仍运行解释器与 AOT 测试。结果记录工具链闭包、
UWVM2 及 Wasm 的摘要。

构建验证上游归档摘要，并以同一编译配置构建 Zend 异常跳转所需的上游
wasi-libc SJLJ 支持。链接阶段封闭文件、描述符及轮询操作，guest 内的兼容
函数拒绝 POSIX 能力调用。VM 仅提供空环境和两种只读时钟，并拒绝退出能力。

首次严格 MTE 构建发现，Zend 的非局部跳转和动态栈分配存在尚无法证明的
所有权路径。MTE 配置选用 Zend 提供的堆分配分支处理长度可变的临时对象。
其余栈生命周期仍由编译器判定，任何编译单元被拒绝都会保留未完成状态。
安装包、线程、memory64、原生 fiber 切换、PHP PHPT 套件、ROS 绑定和设备
部署需要分别验证。

[English](README.md)
