# 移植 ROS 包内资源

C 或 C++ 来宾可以按原来的 `package://` 名称读取打包时选定的文件，无需授予 WASI 文件、网络或环境变量访问权。安装时照常选择语言和平台，传入 `--component migration`，将返回的安装路径设置为 `UWVM_ROS_SDK_ROOT`。该组件包括编译器、Xmake 适配、宿主 Python 工具和头文件 `include/wros/package_resources.h`。

例如移植机器人描述时，将 `ROBOT_DESCRIPTION` 指向包含包清单的源码目录。在 POSIX 构建主机上从自己的项目目录运行以下命令。

```sh
python3 "$UWVM_ROS_SDK_ROOT/tools/migration/package_manifest.py" "$ROBOT_DESCRIPTION/package.xml"
python3 "$UWVM_ROS_SDK_ROOT/tools/migration/package_resources.py" lock \
  --package-root "$ROBOT_DESCRIPTION" --uri package://my_robot/urdf/body.urdf --output resources.lock
python3 "$UWVM_ROS_SDK_ROOT/tools/migration/package_resources.py" pack \
  --package-root "$ROBOT_DESCRIPTION" --lock resources.lock --output resources.bin
```

审阅锁文件中的 URI 和 SHA-256。可以分别重复指定所需的包和 URI。源资源或清单的内容改变后必须重新生成锁。工具拒绝符号链接和有歧义的同名包。URI 区分大小写，空格及非 ASCII 字符使用规范的百分号编码。一个包的容量上限为 64 MiB，最多 65,535 个条目。持有整个资源包的来宾可以读取其中的所有内容，部署密钥和可写状态应单独管理。

将 `resources.bin` 放在这段 C23 源码旁，并配置 SDK 的 include 目录。

```c
#include <wros/package_resources.h>
static const unsigned char resources[] = {
#embed "resources.bin"
};

int read_description(wros_package_view *result) {
    const char uri[] = "package://my_robot/urdf/body.urdf";
    wros_package_index package;
    return wros_package_open(resources, sizeof resources, &package) &&
           wros_package_find(&package, uri, sizeof uri - 1, result);
}
```

索引可以打开一次后反复查询。整个使用期间需要保持资源内存有效且不可变。查询存在的空文件会成功返回零长度。C++ 调用者也可提供相同的字节数组。Xacro 展开和网格解析由调用者负责，它们引用的其他文件需要显式选入。写文件、调用驱动等操作仍通过各自的 VM 权限执行。

清单检查器保留依赖类别、版本约束和原有条件表达式。它能确定待移植的源版本；完整验收还需验证该版本的构建、导入、上游测试及部署行为。

### 核查原包与仿真结果

在 SDK 源码树内运行 `tools/migration/audit_ros_packages.py --corpus CORPUS --output OUT`，逐份读取已取得的 ROS 发行版源码。结果分别列出包清单、同名的其他 XML 文档、缺失源码和异常声明，依赖条件保留在对应的发行版记录中。对缺失的名称，可用 `tools/migration/recover_release_manifests.py --corpus CORPUS --table OUT/packages.tsv --output RELEASES` 解析 Bloom 发布标签，在确定的提交中读取清单并核对包名。这个可选的宿主工具依赖 Git 和 PyYAML，补到的清单只能证明包身份。

`tests/migration/package_resource_corpus.py` 在 native、wasm32 和 wasm64 下逐一读取选中的原文件，两种 Wasm 位宽均测试解释器和 AOT。每个源码版本都有记录，可以追溯选中了哪些资源。应用可执行文件、DDS 语义、驱动及传递依赖需要另外验收。

`tests/migration/resource_urdf_mujoco.py` 可读取以上结果中的 `variants.jsonl.gz`，使用已安装的 MuJoCo SDK 回放 URDF 和同包 STL。每个网格来自相同源码快照，固定内容摘要后在仿真的虚拟文件系统中分配文件名，避免不同目录的同名网格互相覆盖。关节限制、惯量、位姿和网格字节均保留。报告列出仿真器拒绝的模型和需要其他工具的依赖。只有固定关节的模型没有动态自由度。

## 检查旧版观察权限

把旧部署的权限参数按原先顺序保存成 UTF-8 JSON 字符串数组，使用 ROS1 或 ROS2 的完整 global、single、group 参数名。工具识别 grant、set、enable、disable、create 和成员配置。改写部署权限推荐前运行安装目录里的检查器。

```sh
python3 "$SDK/tools/migration/legacy_permissions.py" legacy-grants.json
```

退出码 2 要求人工迁移。报告逐项列出观察者和来源的别名、ROS 后端以及所属目标。旧版服务可用性查询同时核对独立的查询权限和调用权限，还可能要求在有限时间内等待。旧事件观察器绑定独立的来源能力与事件种类。ROSv2 的客户端就绪、图可见性与事件流各有自己的语义。相同名字出现在不同权限组中不能建立这种关联。

退出码 0 表示已识别的参数里没有配对观察声明，退出码 3 表示输入无效或选项超出检查器范围。工具只输出检查报告。迁移实施前仍需核对事件种类、预算、速率、类型标识和传输配置。
