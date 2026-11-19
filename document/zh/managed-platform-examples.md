# 托管语言平台工程

按提交、平台和语言（`csharp`、`fsharp` 或 `vbnet`）安装 SDK；使用 `migration` 组件可取得完整的迁移示例。将 `UWVM_ROS_SDK_ROOT` 设为安装目录。运行 `language/csharp/prepare_host.py --language 语言 --prefix 目录` 准备 .NET 和 Mono 宿主，再按语言指南设置 `WROS_DOTNET`、`WROS_MONO`、`WROS_TOOLCHAIN`、`WROS_VM`。将 `examples/platform/<平台>/extension/<语言>` 或相应的 `migration` 目录复制到可写位置，在项目中执行：

```sh
xmake f -c -y -a wasm32
xmake -j1
xmake test -j1
```

扩展示例使用 `--driver-entry Class.Method` 绑定 `Policy(Wros.Scene.DriverConnectionStatus("arm"))`。编译器在 ECMA-335 元数据中核对两个托管调用和别名字面量，通过 Mono 与 LLVM 编译用户编写的状态判断。别名遵守 VM 的 ASCII 标识符规则，长度 1–255，可用字母、数字、下划线、短横线与点，保留 `.` 和 `..`。绑定先取得指定的父能力，再实际尝试连接驱动。拒绝时检查响应区和长度槽是否保持原值；返回其他状态时尝试断开。最后关闭句柄，清零临时数据。清理失败或检测到拒绝时修改输出，将触发陷阱。对同一所有者已有的会话，此调用可能将其断开。请给此有界检查单独分配设备别名和会话。模块保留一页私有线性内存，使用四个固定导入，所需运动控制、文件系统权限均为零。托管策略只接收整数状态码。

测试夹具在每次运行时提供认证本机套接字、新密钥和指定平台子权限。INT 和 AOT 都分别验证了父权限不足和子项禁用。程序要求返回权限错误码 13，外部测试端必须收到零字节。该测试检验权限控制与语言绑定。迁移工程则通过场景 ABI 授权检查 ROS 1 actionlib 的十个状态值。[迁移语义](platform-migration-examples.md)。
