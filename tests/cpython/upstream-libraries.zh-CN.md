# Wasm SDK 的 Python 上游库测试

此测试执行 ROS `angles` 1.16.1 原版 Python 实现和全部 7 个单测方法，固定
提交为 `a96224f9ab3ac51fe8fd981c1e1554528dc4345a`。同时执行 PyPA
`packaging` 25.0 的 21 个版本测试方法，共 555 次调用，固定提交为
`f58537628042c7f29780b9d33f31597e7fc9d664`。执行前验证 Git 提交和源码归档摘要。
[ROS angles](https://github.com/ros/angles/tree/a96224f9ab3ac51fe8fd981c1e1554528dc4345a)。
[PyPA packaging](https://github.com/pypa/packaging/tree/f58537628042c7f29780b9d33f31597e7fc9d664)。

按英文版命令获取源码，使用现有的 64 GiB cgroup 门控，并选择 `.tmp` 下
的新输出目录。已安装 SDK 必须选择匹配 VM 的 wasm32 Core 3.0、单线程、
EH、严格 MTE、`-O3 -g` C 站点及相应的 CPython 运行时包。

本机参考和 Wasm 使用相同的上游断言。guest 直接使用 CPython 3.14.8 的
`unittest.TestCase` 和 `TestResult` 实现。`packaging` 适配器保留原始测试
函数体，并重放上游的字面量参数。结果中列明额外依赖 pytest、pretend 或
非字面量参数的 5 个未纳入方法。

最终 Wasm 只导入两个只读 Preview 1 时钟函数。同一个模块在 UWVM2
解释器和 AOT 下以同步 MTE 执行，并记录 Python 运行时及 Wasm 摘要。
验收范围是这两个纯 Python 库的上述行为。ROS 通讯、其他 packaging
测试文件、memory64、线程和部署需要各自的验证。

[English](upstream-libraries.md)
