# Java 和 Kotlin 的 AOT 后端

[English](README.md)

TeaVM 0.13.1 读取 Java 或 Kotlin 编译器生成的 JVM 字节码。WROS 移植使用其 C 后端生成供 WROS Clang 和 Wasm 链接器处理的代码。后端同步调用应用入口，保留 guest 引用的完整位宽，内存由 Wasm 侧的非移动式收集器管理。Java 驱动保留源文件位置，遇到严重编译问题时返回失败。[驱动](driver/Translate.java) · [C 后端](upstream/core/src/main/java/org/teavm/backend/c/CTarget.java) · [分配器](upstream/core/src/main/java/org/teavm/runtime/Allocator.java)

[源码清单](upstream.json)给出官方标签、完整提交、压缩包摘要，以及 14 个修改文件各自在修改前后的摘要。编译器、标准类库、工具、Unicode 和时区数据均在 upstream 目录中。清单逐项列出省略的 IDE 文件与预编译 Gradle wrapper JAR。审阅或构建 Gradle 项目时使用 Gradle 9.1.0 和兼容的 JDK。[构建配置](upstream/settings.gradle.kts) · [依赖版本](upstream/gradle/libs.versions.toml) · [Apache-2.0 许可证](upstream/LICENSE)

x86-64 宿主 Java 前端选用 Eclipse Temurin 21.0.10+7。项目内已收入 OpenJDK 编译器模块、HotSpot、JDK 构建文件和对应的 Adoptium 发行构建脚本。所选的 25,333 个 JDK 文件及全部 146 个发行构建文件已逐项核对官方 Git blob 和文件模式。省略的 JDK 根目录条目为 `.github`、`.jcheck` 和 `test`。各模块和第三方组件的许可证随源码保留。[javac 入口](openjdk/upstream/src/jdk.compiler/share/classes/com/sun/tools/javac/Main.java) · [OpenJDK 构建说明](openjdk/upstream/doc/building.md) · [发行构建脚本](openjdk/temurin-build/README.md) · [提交和许可证](openjdk/upstream.json)

## Java 编译器发行物

原生 ELF 入口 `wrjava` 调用所选宿主的 JDK，使用 javac 编译用户代码、移植后的 TeaVM 生成 C，再由 WROS C 编译器链接。五个宿主各自的 `bin/packages/<host>/wrjava/java.json` 锁定 WROS 入口并指定上游 JDK 清单。静态入口由固定的 Zig 0.15.2 生成，源码模式可以用本机 C11 编译器重新编译入口。英文说明给出完整的重建参数。[入口和依赖重建](README.md) · [安装与 Xmake](../../../document/zh/languages/java.md)

x86-64 安装器使用 Adoptium 发布的 Temurin JDK 21.0.10+7，核对原始 gzip 包、完整 tar 字节流和关键 JDK 文件。i686、AArch64、ARM 软浮点、ARM 硬浮点分别使用 Debian i386、arm64、armel、armhf 的 `openjdk-21-jre-headless` 和 `openjdk-21-jdk-headless` 21.0.10+7-1~deb13u1。锁文件记录了 2026 年 1 月 28 日的 Debian 安全仓库快照和签名索引中的摘要。安装器用 `dpkg-deb` 提取 java、javac、javap、模块映像、运行库、配置和许可证，解析包内链接并核对 ELF ABI。宿主提供对应架构的 JRE 系统库，其中 armel 的 Zero VM 需要 libatomic。安装映像省略 Debian 源码 ZIP 链接和由系统管理的网络信任库。[Debian 官方输入、架构和摘要](openjdk/debian/upstream.json) · [Temurin 来源](openjdk/upstream.json)

两种模式均从 Maven Central 取得 29 个编译依赖 JAR，安装到 `share/toolchains/teavm/jars`。类路径优先使用 WROS 编译的类和运行时模板。源码模式还获取 11 个外部依赖的源码 JAR。使用 Debian JDK 的宿主会将对应源码压缩包恢复到 `src/compilers/jvm/openjdk/debian` 中的签名 `.dsc` 旁。在该目录运行 `dpkg-source -x openjdk-21_21.0.10+7-1~deb13u1.dsc` 可展开源码和 Debian 补丁。所有官方输入均按大小和 SHA-256 验证，后续安装复用 `<prefix>/.cache/sha256/<sha256>` 下的文件。缓存齐备时，安装器可以从本地获取全部 Java 输入。[依赖锁](java-jars.json) · [外部依赖源码](java-source-jars.json) · [安装器](prepare.py) · [Debian JDK 文件选择](package_inputs.py)

五种 WROS 入口的清单均锁定可执行文件和压缩包摘要。从官方输入安装、两种 VM 引擎、部署器、所选原生工具链源码重建和上游 JDK、Gradle 发行物重建仍待独立验收。Kotlin 需要单独的前端。
