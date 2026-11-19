# 用旧 ROS 的 C++ 原始测试验证 Wasm 移植

从本地 ROS 源码清册读取指定发行版归档，校验 SHA-256，再提取上游测试翻译单元和它在包内引用的头文件。源码相对路径和内容摘要都相同时，多个归档共用一次执行结果。收据记录每个归档的来源、分支、包清单路径、缺失的翻译单元和未选取的测试。

本组测试覆盖 `angles` 的角度归一化及边界、`base_local_planner` 的网格与速度迭代器、`rcpputils` 的累加、区间截取及指针类型工具，以及 `nav_core2` 的矩形边界。验证范围限于列出的 C++ 用例。ROS 节点、DDS、物理设备和包内其他程序需要单独验收。

`VelocityIteratorTest.test_cranky` 的原始测试只写入 4 个值，随后比较 5 个值，其中最后一个未初始化。对于已经核对过摘要的测试文件，运行器将测试自己的数组初始化为零，保留全部比较，并分别记录原始与修订文件摘要。第 5 次比较只能验证测试数组的初值。迭代器的有效输出仍为 4 个。原用例单独记为未通过资格审查。

第一份原生基线使用归档内的 GoogleTest 构建，通过 XML 核对每个测试确实执行成功。第二份原生程序在执行原断言时，逐用例记录断言数量和按执行顺序计算的 64 位摘要。Wasm 解释器和 AOT 运行相同测试正文，并核对每个断言、总数和顺序摘要。断言失败会触发 trap。测试程序仅使用 guest 自有内存，要求最终 Wasm 模块的导入表为空。

从 VM 仓库执行下列命令。各路径使用绝对路径，输出选择项目 `.tmp` 下的全新目录。`--yield-lock` 在两批独立测试之间释放同一把资格测试锁。

```sh
/usr/bin/python3 tools/ros_scene/in_existing_cgroup.py /usr/bin/taskset -c 4-7 \
    /usr/bin/flock "$SDK/.tmp/sdk-qualification.lock" /usr/bin/python3 -B \
    "$SDK/tests/migration/upstream_cpp.py" --yield-lock "$SDK/.tmp/sdk-qualification.lock" \
    --corpus "$CORPUS" --sdk "$INSTALLED_CPP_SDK" --toolchain "$TOOLCHAIN" \
    --sysroots "$SYSROOT_RECEIPT" --vm "$VM" --output "$SDK/.tmp/upstream-cpp-run"
```

默认使用通过审核的严格 MTE 配置，目标为单线程 wasm32、C++17、EH 和 `-O3 -g`。运行器会逐个核对产物、编译收据和 VM 摘要。选择性安装 SDK 后，可传入 `--installation-receipt` 和安装命令的 JSON 输出文件，记录实际的编译器 SDK 提交与平台。显式传入 `--legacy-mte` 会记录为开发用配置，其结果仅支持该配置。

在相同 cgroup、CPU 和锁下执行 `tests/migration/upstream_cpp_report.py INPUT/results.json OUTPUT.json` 生成各包统计。报告按源码及头文件的唯一组合计数，分别列出未改动用例、经修订用例、重复归档、未选取文件、原生与 Wasm 产物摘要，以及实际运行结果。

使用另一个已签署的编译器和 VM 时，可在相同 cgroup 和锁内运行 `tests/migration/upstream_cpp_replay.py`，传入 `--previous INPUT/results.json`、`--sdk`、`--installation-receipt`、`--toolchain`、`--sysroots`、`--vm` 和 `--output`。它先复核已完成的原生基线、源码和产物摘要、GoogleTest XML 及断言轨迹，再从相同源码重建所有 Wasm 程序，逐件核对产物、编译收据、VM 摘要及已签署的工具链资格，再在两个引擎执行。收据记录复用的原生结果摘要。

## 深度图像 RVL

`tests/migration/depth_rvl.py` 使用独立的格式参考编码器核对
`compressed_depth_image_transport` 的 RVL 实现。在验收 cgroup 和共享 SDK
验收锁下，从 SDK 仓库执行下列命令。参数依次指定 ROS 源码语料、已安装且
具备严格 wasm32 MTE 配置的 C++ SDK、与配置匹配的 VM，以及 `.tmp` 下的新目录。

```sh
/usr/bin/python3 -B tests/migration/depth_rvl.py \
  --corpus "$ROS_SOURCE_CORPUS" --sdk "$INSTALLED_CPP_SDK" \
  --vm "$UWVM_ROS" --output "$PWD/.tmp/depth-rvl"
```

脚本检查各快照的归档摘要，按实现和头文件的实际内容归并。本轮 16 个快照有
6 个包含 RVL，其中 Indigo 与 Noetic 共享一份实现，Jazzy、Kilted、Lyrical
与 Rolling 共享另一份。两份实现分别处理空帧、全零、常值、正负极差、
变长编码边界和合成扫描线。测试逐字比较压缩结果，逐像素检查解码结果。
更改一个预期编码字后，原生程序必须返回错误，同一个无宿主导入的严格
Wasm 模块必须在解释器和 AOT 中均触发陷阱。

结论限于小端平台和本地生成的有效 RVL 帧。上游解码 API 接收像素数，
没有压缩输入长度参数。接收外部帧、ROS 图像传输插件、PNG 及其他包内源码均需单独验证。

## 刚体坐标变换

`tests/migration/tf2_transforms.py` 与 RVL 测试使用相同的 `--corpus`、`--sdk`、
`--vm`、验收 cgroup 和共享锁，另行指定新的 `--output` 目录。脚本从各归档
选取原版 tf2 LinearMath 头文件，包括 Groovy 的 Bullet 接口。需要
`ros/macros.h` 的旧版本使用记录了摘要的 ROS `cpp_common` 源码快照。本轮核对了语料中的全部 22 个 tf2
快照，并分别执行了按文件内容归并后的 13 组头文件。

八组姿态验证父子坐标变换的组合、原点、求逆、逆向作用于点、相对变换及
从四元数还原姿态。其中包含次序不可交换的旋转、光学坐标系、接近零度或
半周的旋转，以及表示相同方向的非单位四元数。Python 参考算法从轴角出发，
使用 Rodrigues 公式计算预期坐标。C++ 程序运行时读取输入，在原生、解释器
和 AOT 三个环境逐项比较结果。将一项预期坐标偏移一米，三个环境都必须
检测出错误。本组姿态的绝对误差限分别为单精度 0.00003 米、双精度
0.00000000002 米。时间缓冲查询、坐标树控制权限和 DDS 传输需要各自的联测。

## Jazzy BufferCore 与变换历史

`tests/migration/tf2_buffer_layers.py` 从校验了摘要的语料归档构建 Jazzy 原版
`tf2` 和 `rcutils`。BufferCore 还使用 Jazzy 安装中的 C++ 消息头文件。
原生测试编译上游源文件；Wasm 测试使用所选的严格 MTE SDK。在验收 cgroup
和共享锁下分别执行各组合。

```sh
/usr/bin/python3 -B tests/migration/tf2_buffer_layers.py \
  --layer buffer --target native --corpus "$ROS_SOURCE_CORPUS" \
  --sdk "$INSTALLED_CPP_SDK" --vm "$UWVM_ROS" \
  --ros-prefix "$JAZZY_PREFIX" --output "$PWD/.tmp/tf2-buffer-native"
```

`--layer cache` 选择原版 `TimeCache`；`--target wasm` 同时测试解释器和
AOT。每次指定新目录。构建失败时保留编译器原文和 `complete=false` 的记录。
测试使用确定性的时间戳。

| 层 | 原生 | 严格 wasm32、无线程 |
| --- | --- | --- |
| BufferCore | 通过乱序插入、动静两段变换插值、最新时间、断开树、前后超界及清空查询 | 构建受阻。BufferCore 需要的 `std::mutex` 和 Jazzy 消息头使用的 `std::wstring_convert` 未在该 C++ sysroot 提供 |
| TimeCache | 通过乱序插入后的按时间查询、插值、最新时间、外推拒绝、剪除过期记录及清空 | 解释器和 AOT 均通过，所有导入的 WASI 操作均设为拒绝 |

故意把插值预期偏移一米时，原生程序返回错误，Wasm 时间缓存在两个引擎
均触发陷阱。C++ 库保留了 `environ_get`、`environ_sizes_get`、
`clock_time_get` 和 `proc_exit` 四个导入，均使用单模块 `deny`，未授予
文件系统、套接字、环境或时钟的操作权限。WASI 构建在一个翻译单元中
选择上游 `rcutils` 的 XSI `strerror_r` 分支。BufferCore 测试使用原版
日志宏的 `NONE` 编译级别。DDS 接收、日志、线程配置及并发修改树仍需验证。

C++ 迁移组件另提供了按摘要验证的 Jazzy BufferCore 适配。Wasm 坐标树测试可添加
`--port single-executor` 测试单执行器，或添加 `--port threaded` 测试保留原版
互斥锁的配置。原版结果使用默认的 `--port upstream`。见[安装及构建说明](tf2-buffer-port.md)。
