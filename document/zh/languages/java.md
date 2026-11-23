# 编译 Java 客户程序

`--language java --platform abb` 安装 ABB ROS 1 观测接口，`--platform generic` 安装通用场景接口。SDK 为 Linux x86-64、i686、AArch64、ARM 软浮点和 ARM 硬浮点提供原生 `wrjava` 入口。安装器在 x86-64 上从 Eclipse Temurin 获取 JDK，其余四种宿主使用 Debian Snapshot。Debian 宿主需要 `dpkg-deb` 和对应 JRE 的系统动态库。完整流程还需匹配的 WROS C 编译器、Xmake 和 VM。独立安装、INT、AOT 和部署器验收均待完成。

将 REV 设为完整的发行提交号，使用 Python 3.11 或更高版本。安装器返回实际选择目录。

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
python3 -I -B install.py install --commit "$REV" --platform abb --language java --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
cp -R "$UWVM_ROS_SDK_ROOT/examples/abb/java" abb-java
cd abb-java
wrjava --main-class example.Guest --source-root src --keep-work build-inputs -o abb-state.wasm
xmake build
xmake test -j1
```

本地冻结提交可在检出根目录运行 `python3 -I -B install/install.py "$PWD" "$REV" "$PWD/sdk" install --language java --platform abb`。两种安装入口都从锁文件记录的发行方和 Maven Central 获取对应 JDK 和 29 个编译依赖 JAR，每个文件均核对大小和 SHA-256。要复用本地 Java 输入，可将这些官方文件和所需 Git LFS 对象按摘要存入 `<prefix>/.cache/sha256/<sha256>`。安装后，客户程序构建使用 SDK 内的 JDK、JAR、原生编译器和头文件。[Temurin 锁](../../../src/compilers/jvm/openjdk/upstream.json) · [Debian 锁](../../../src/compilers/jvm/openjdk/debian/upstream.json) · [编译依赖锁](../../../src/compilers/jvm/java-jars.json)

Xmake 用 `set_wros_main_class("your.package.Main")` 设置用户入口，用 `add_files` 声明实际源码。直接调用可传多个 Java 文件或多次指定 `--source-root`。`--keep-work` 使用一个新目录，其下的 `classes`、`generated` 分别保留字节码和生成的 C。客户 ABI 固定为 wasm32、Core 3.0、启用 memory64 特性、EH、MTE、单线程。

通用的 `u2rosv2.Scene` 提供 ABI 查询、能力句柄的打开与关闭，以及读取受授权的时钟。ABB 工程提供 14 种 ROS 1 消息和服务正文类型。[通用接口](../../../include/u2rosv2/universal/java/src/u2rosv2/Scene.java) · [ABB 类型和示例](../../../include/u2rosv2/platform/abb/java/README.md)

二进制模式安装原生 `wrjava` 入口，用所选 JDK 编译 WROS 的 TeaVM 源码改动。源码模式还使用宿主 C11 编译器（`CC`，默认 `cc`）重建入口，安装 TeaVM 和 OpenJDK 源码，并从 Maven Central 获取 11 个外部依赖的源码 JAR。使用 Debian JDK 的宿主还从同一 Debian Snapshot 恢复相应源码包。上游发行物重建和 Java 标准库行为仍待验收。[源码与构建配方](../../../src/compilers/jvm/README.zh.md)
