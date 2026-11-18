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
