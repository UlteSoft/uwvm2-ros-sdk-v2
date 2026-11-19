# 构建并运行平台迁移示例

每个注册平台都在 `examples/platform/<平台>/migration/<语言>` 下提供 C 和 F# 项目。安装时选择所需的平台和语言，将项目复制到可写目录，再使用 Xmake 编译并测试。C 示例验证 ROS 包资源迁移，F# 示例验证 ROS 1 动作客户端状态判断。

## 安装与运行

设置 `REV` 为 SDK 提交、`PREFIX` 为安装目录、`PLATFORM` 为平台标识。C 工具链使用经本机信任的签名站点配置，配置中包含 wasm32 MTE/EH 编译器与 sysroot 的位置。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform "$PLATFORM" \
    --language c --prefix "$PREFIX" --site-profile "$C_SITE" -- --component migration
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/$PLATFORM/c/migration"
export WROS_VM=/绝对路径/uwvm2-ros
cp -R "$UWVM_ROS_SDK_ROOT/examples/platform/$PLATFORM/migration/c" ./resource-example
cd resource-example
xmake f -c -y -a wasm32
xmake -j1
xmake test -j1
```

默认使用随示例分发的 ROS 2 `sensor_msgs` 包清单与 `msg/Imu.msg`。要运行对应平台 README 指定的上游资源，将 `WROS_ROS_PACKAGE_ROOT` 指向该版本的包清单所在目录，然后重新构建并测试。外部提供的厂商包仅在本机读取。宿主核对 `upstream.lock` 中的资源和清单 SHA-256。Wasm 检查 URI 精确查找、字节数、完整内容校验和与缺失资源的返回值。该示例所需的文件系统和网络权限均为零。

安装 F# 示例时，指定 `--language fsharp` 和相同的 `migration` 组件，省略 C 站点配置，准备固定版本的 Microsoft SDK 和 Mono 编译器。

```sh
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/$PLATFORM/fsharp/migration"
python3 "$UWVM_ROS_SDK_ROOT/language/csharp/prepare_host.py" --language fsharp --prefix "$HOST_TOOLS"
export WROS_DOTNET="$HOST_TOOLS/dotnet" WROS_MONO="$HOST_TOOLS/compiler"
export WROS_TOOLCHAIN=/绝对路径/wasm-llvm
export WROS_VM=/绝对路径/uwvm2-ros WROS_RUN_QUERIES=abi
cp -R "$UWVM_ROS_SDK_ROOT/examples/platform/$PLATFORM/migration/fsharp" ./goal-example
cd goal-example
xmake f -c -y -a wasm32
xmake -j1
xmake test -j1
```

F# 客户端遍历 ROS 1 的十个线协议状态值，检查进入终态的六个值 PREEMPTED、SUCCEEDED、ABORTED、REJECTED、RECALLED 和 LOST。LOST 由客户端判定。遍历从实际读取的场景 ABI 开始，并检验主机 ABI 为 2。测试只授予 ABI 查询权限。设备控制、DDS 通信和机器人物理动力学需分别验收。[ROS 1 状态定义](https://github.com/ros/common_msgs/blob/092bc230c8153dd4cfee0c84c9796cc7e6b09fdb/actionlib_msgs/msg/GoalStatus.msg) 与 [actionlib 客户端终态语义](https://github.com/ros/actionlib/blob/noetic-devel/actionlib/include/actionlib/client/simple_client_goal_state.h)。
