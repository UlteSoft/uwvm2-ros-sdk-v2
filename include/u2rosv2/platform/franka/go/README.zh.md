# 在 Go 和 TinyGo 中使用 Franka ROS 2

`github.com/UlteSoft/uwvm2-ros-sdk-v2/franka` 模块按固定的 53 份 ROS 2 声明提供 137 个记录及其 XCDRv1 PLAIN_CDR 编解码器。标准 Go 1.24.2 和 TinyGo 0.38.0 使用同一本地模块。每份生成文件都链接上游原始声明，并用英文标注字段单位、参考坐标系、取值或协议含义。[English](README.md) · [平台 CDR 手册](../../../../../platform/franka/cdr.zh.md)

## 消息和服务

- `.../franka/cdr/frankamsgs` 提供 77 个记录，涵盖机械臂状态、阻抗、碰撞阈值、负载、坐标系、夹爪及点到点运动动作。`FrankaRobotState.MeasuredJointState` 保存关节名称、位置（rad）、速度（rad/s）和连杆侧力矩（N·m）。Franka 语义组件从 libfranka 状态写入这些字段，设置基座参考坐标系，并在同一条记录中发布肘部、位姿、惯性、力旋量及加速度计字段。`GraspFeedbackMessage` 将目标 UUID 和当前夹爪宽度（m）配对。[Franka 语义组件](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_semantic_components/src/franka_robot_state.cpp) · [Grasp 动作](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_msgs/action/Grasp.action)
- `.../franka/cdr/frankaspinemsgs` 提供 35 个记录，涵盖脊柱状态、位置、用户行程限制、七项服务及 MoveAbsolute 动作。`GetPositionResponse.Position` 用米表示。`GetPositionEvent` 将可选的请求、响应与客户端 GID 和序列号关联。[脊柱消息及服务定义](https://github.com/frankarobotics/franka_ros2/tree/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_spine/franka_spine_msgs)
- 其余 25 个记录分布于 `cdr/actionmsgs`、`cdr/builtininterfaces`、`cdr/geometrymsgs`、`cdr/sensormsgs`、`cdr/servicemsgs`、`cdr/stdmsgs` 和 `cdr/uniqueidentifiermsgs`。嵌套字段直接使用这些包中的类型。例如 `actionmsgs.GoalStatusArray.StatusList` 是目标状态切片，`servicemsgs.ServiceEventInfo.ClientGID` 是 16 字节数组。每个动作均包含 Jazzy rosidl 展开的 Goal、Result、Feedback、FeedbackMessage 和两个服务的请求、响应、自省事件。[Jazzy rosidl 记录定义](https://github.com/ros2/rosidl/blob/9bcfabf3eddf8e63fb4332dca6da7ec6f3140d65/rosidl_parser/rosidl_parser/definition.py)

Go 组件类型省略下划线。例如，`frankamsgs.PTPMotionSendGoalRequest` 的 `ROS2Type()` 返回 `franka_msgs/action/PTPMotion_SendGoal_Request`。结构体的 `ros` 标签保留原字段名称，常量保留声明的整数宽度。Go 零值将数值字段置零。需要声明中的默认值时，`DefaultGraspGoal()` 将夹爪内外容差均设为 0.005 m，`geometrymsgs.DefaultQuaternion()` 将 W 设为 1。构造函数也递归初始化嵌套字段。[夹爪容差声明](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_msgs/msg/GraspEpsilon.msg) · [四元数声明](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/Quaternion.msg)

## 帧边界和所有权

`UnmarshalCDR(frame)` 与 `UnmarshalBinary(frame)` 接受包含四字节封装头的完整帧，从标识符读取大端或小端序。所有嵌套标量均从封装头后的第一个字节开始对齐。定长数组直接存放全部元素。序列以 uint32 记录元素数，服务事件的请求和响应各最多一个元素。字符串的 uint32 字节数包含末尾 NUL。Go 字符串保留此前的全部字节，包括内嵌 NUL。布尔值只接受 0 和 1。空 rosidl 组件包含一个字节的占位字段。[CDR 封装与尾部填充](../../../../../platform/franka/cdr.zh.md)

解码器先扫描完整帧，检查长度能否用本机整数表示、剩余载荷能否容纳声明的元素、序列上界和尾部填充，再分配字符串及切片。调用返回前请保持源帧稳定。成功后字符串和切片均由结果持有，输入缓冲区可以立即复用。解码得到的空序列为 nil 切片。解码失败时接收对象保留原值。`frankamsgs.ValidateElbow(frame)` 及其他记录对应的验证函数可直接校验完整帧，无需创建动态字段。

`CDRSize()` 给出含四字节头的总长度。`MarshalCDR(cdr.BigEndian, dst)` 和 `MarshalCDR(cdr.LittleEndian, dst)` 先测量长度并验证缓冲区容量，随后写入，返回已写字节数。写入期间保持源对象稳定且与输出不重叠。`MarshalBinary()` 分配等长的小端帧。编码时对齐填充与封装选项均写零。解码接受低两位给出的尾部填充数，传输层可以保留或剥除该填充。填充数与载荷长度不一致时返回 `cdr.ErrPadding`，遇到额外字节时返回 `cdr.ErrTrailing`。

## 构建外部工程

在 Linux x86-64 的空目录中使用 Python 3.11 或更高版本、Git 和 curl。以下命令固定到正在独立验收的 Franka 公开候选。标准 Go 工程对两份独立的 84 字节 Fast-CDR Elbow 帧进行双向转码，并按语义组件布局解码机械臂状态。TinyGo 工程读取夹爪反馈及 0.42 m 的脊柱位置服务响应。两个工程均从客体读取场景 ABI，消息载荷来自本地缓冲区。[Elbow 帧的参考实现](https://github.com/eProsima/Fast-CDR/tree/9f4e60f7ac958e0fbbfe949102de3929cbbc226f) · [上游脊柱示例](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_spine/franka_spine_server/test/test_spine_controller.py#L311)

```sh
set -eu
revision=17ff81a1662824a25f81cd056c02232dfbe23541
curl -fLsS --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
export GOPROXY=off
unset WROS_VM XMAKE_PROGRAM_DIR

for language in go tinygo; do (
    python3 -I -B install.py install --commit "$revision" --platform franka --language "$language" \
        --prefix "$PWD/sdk" > "$language-selection.json"
    export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["directory"])' "$language-selection.json")"
    cp -R "$UWVM_ROS_SDK_ROOT/examples/franka/$language" "$language-project"
    cd "$language-project"
    case "$language" in go) compiler=wrgo ;; tinygo) compiler=wrtg ;; esac
    "$UWVM_ROS_SDK_ROOT/bin/$compiler" . -o direct.wasm
    for engine in int aot; do
        python3 -I -B "$UWVM_ROS_SDK_ROOT/tools/xmake/run_guest.py" direct.wasm \
            --engine "$engine" --core 3.0 --mte --eh --memory64 --no-threads --query abi --query go-runtime
    done
    "$UWVM_ROS_SDK_ROOT/bin/xmake" build
    "$UWVM_ROS_SDK_ROOT/bin/xmake" test -j1
); done
```

所选 SDK 自带原生 `wrgo` 或 `wrtg`、Xmake、VM 及 Go 模块。编译驱动将工程 `go.mod` 中的公共模块映射到当前安装目录。在 SDK 源码仓中运行 `python3 -B src/platform/franka/generate_go.py` 可根据固定的声明、源码摘要、英文注释和 `gofmt` 重新生成分域代码。
