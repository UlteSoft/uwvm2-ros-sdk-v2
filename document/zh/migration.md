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
