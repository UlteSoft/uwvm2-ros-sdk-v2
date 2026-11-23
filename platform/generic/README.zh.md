# 通用 ROS 场景

此选择适用于调用 `uwvm_ros_v2` 场景 ABI 的 guest。安装目录中的 `share/abi/ros.json` 记录导入名与 Wasm 函数签名。`examples/<language>` 查询 VM 的 ABI 版本，收到的值与 2 不同时触发 trap。示例 Xmake 工程为本地测试授予 `abi` 查询。JavaScript 和 TypeScript 工程还为 QuickJS 申请 WASIp1 实时时钟。
