# Java 与 Kotlin 同步 AOT

可选组件 `synchronous-aot` 将应用、可达类库与回收器编译到一个 wasm32 core 模块。仅构建宿主运行 JDK 21、Kotlin 编译器和 TeaVM 0.13.1。VM 内执行的产物是 Wasm。此组件尚无已签署的受管近邻资格。默认构建、关闭 MTE、wasm64 与线程均被拒绝，显式 `--legacy-mte` 生成带 WasmMTE 的程序并打印提示。

使用完整 SDK 提交、平台和语言运行固定入口安装脚本，在 `--` 后传入 `--component synchronous-aot`。安装目录结尾为 `<平台>/<java或kotlin>/synchronous-aot`。该目录包含所选语言、对应 Xmake 适配、共享 AOT 与运行时源码、示例和宿主输入哈希。使用旧 SDK 固定的 Linux x86-64 JVM 宿主包，依据 `language/<语言>/host-inputs.json` 逐文件校验。Java 使用的类路径仅包括清单中的 JAR，不依赖 Kotlin 编译器。另需匹配的 LLVM 及 wasm32 单线程 EH sysroot。

可以从 Ubuntu OpenJDK 21.0.10+7-Ubuntu-125.10、与清单匹配的系统库和 Maven 依赖生成单语言宿主包。脚本优先读取本地 Maven 缓存，也支持从 `--jars DIR` 指定的平铺目录取包。显式使用 `--fetch-missing-jars` 时只从 Maven Central 下载本语言清单内缺少的 JAR。所有文件的长度与 SHA-256 校验成功后才发布输出目录。以下路径对应已验证的 Linux x86-64 宿主。

```sh
python3 "$UWVM_ROS_SDK_ROOT/language/jvm/prepare_host.py" java \
  --jdk /usr/lib/jvm/java-21-openjdk-amd64 --system-libs /usr/lib/x86_64-linux-gnu \
  --fetch-missing-jars --output "$BUILD_DIR/java-host"
export WROS_JVM_BUNDLE="$BUILD_DIR/java-host"
```

Kotlin 用户将 `java` 换成 `kotlin`。Java 选择 29 个 JAR，Kotlin 选择 36 个。已有的开发宿主包也可以按 `--jdk`、`--system-libs`、`--jars` 三个目录提供离线输入。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrkotlin" --legacy-mte --main-class example.Main \
  --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --bundle "$WROS_JVM_BUNDLE" \
  --work "$BUILD_DIR/kotlin-log" -o "$BUILD_DIR/body.wasm" Main.kt
```

Java 使用 `wrjava`、`.java`；Kotlin 可用 `@file:JvmName("Main")` 指定 JVM 入口类名。`--work` 可选，目录须尚未存在，保留命令、日志、源码哈希及最终导入。前端固定采用 `-O3 -g`，Java 分配预算 16 MiB、线性内存上限 256 MiB。先检查应用字节码，再生成 C 并链接到 Wasm。

项目示例见 `examples/<语言>/synchronous-aot/xmake.lua`。令 `UWVM_ROS_SDK_ROOT` 指向安装目录，并设置 `WROS_TOOLCHAIN`、`WROS_SYSROOTS`、`WROS_JVM_BUNDLE`。`set_wros_jvm_main("example.Main")` 指定入口，`set_language`、`add_files` 选择语言与源文件，设置 `set_optimize("fastest")`、`set_symbols("debug")`、Core 3.0、EH、无线程和 `mte = "legacy"`。

示例展示 ABI 查询及具有单独授权的 guard。`Guard.open(byte[])`、`create()`、`trigger()`、`take(long[])`、`close()` 返回 VM 状态码，take 的输出数组须有一个元素。授予资源别名和具体操作后才能使用。Java 实时和单调时钟分别申请 WASIp1 的只读时钟权限。

应用可使用受支持的局部类、基本运算、数组、显式回收和文档中的宿主操作。应用字节码中的其他外部调用、原生方法、动态调用、监视器和异常捕获在编译阶段被拒绝；未处理的异常终止 guest。完整反射、完整类库、直接缓冲区、JNI、文件和网络 I/O、线程及工业安全部署资格均尚未提供。

固定版本的宿主 JVM 使用解释执行并关闭 core dump。生成的客体始终经过带优化的 Wasm AOT 编译器。
