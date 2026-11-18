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
"$UWVM_ROS_SDK_ROOT/bin/wrkt" --legacy-mte --main-class example.Main \
  --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --bundle "$WROS_JVM_BUNDLE" \
  --work "$BUILD_DIR/kotlin-log" -o "$BUILD_DIR/body.wasm" Main.kt
```

Java 使用 `wrjava`、`.java`；Kotlin 可用 `@file:JvmName("Main")` 指定 JVM 入口类名。`--work` 可选，目录须尚未存在，保留命令、日志、源码哈希及最终导入。前端固定采用 `-O3 -g`，Java 分配预算 16 MiB、线性内存上限 256 MiB。先检查应用字节码，再生成 C 并链接到 Wasm。

项目示例见 `examples/<语言>/synchronous-aot/xmake.lua`。令 `UWVM_ROS_SDK_ROOT` 指向安装目录，并设置 `WROS_TOOLCHAIN`、`WROS_SYSROOTS`、`WROS_JVM_BUNDLE`。`set_wros_jvm_main("example.Main")` 指定入口，`set_language`、`add_files` 选择语言与源文件，设置 `set_optimize("fastest")`、`set_symbols("debug")`、Core 3.0、EH、无线程和 `mte = "legacy"`。

示例展示 ABI 查询及具有单独授权的 guard。`Guard.open(byte[])`、`create()`、`trigger()`、`take(long[])`、`close()` 返回 VM 状态码，take 的输出数组须有一个元素。授予资源别名和具体操作后才能使用。Java 实时和单调时钟分别申请 WASIp1 的只读时钟权限。

应用可使用受支持的局部类、基本运算、数组、显式回收和文档中的宿主操作。应用字节码中的其他外部调用、原生方法、动态调用、监视器和异常捕获在编译阶段被拒绝；未处理的异常终止 guest。完整反射、完整类库、直接缓冲区、JNI、文件和网络 I/O、线程及工业安全部署资格均尚未提供。

固定版本的宿主 JVM 使用解释执行并关闭 core dump。生成的客体始终经过带优化的 Wasm AOT 编译器。

### 隔离驱动会话

`wros.scene.Driver` 通过部署器预置的别名连接驱动。`open(byte[] alias, int requestLimit, int responseLimit)` 的两个长度上限均为 0 至 65,536 字节。响应上限应至少覆盖部署登记的响应容量。先执行 `connect()`，再调用 `submit(long sequence, long deadline, byte[] payload)` 提交该注册协议规定的载荷与单调时钟的绝对截止时间。部署须分别授权相应的接口和资源。

`result(long sequence, byte[] payload, long[] outcome)` 需要至少覆盖所选响应上限的字节数组，以及两个结果字。成功时写入驱动状态、实际字节数和响应内容。拒绝时保留调用方数组内容。方法本身返回 VM 操作状态。`describe(long[4])` 提供阶段、序号、状态、效果未知位。`disconnect()` 断开传输，`close()` 释放本地能力。部署器持有驱动生命周期和 TLS 身份，包装层每次使用后清零自己的消息暂存区。

运行 `tests/jvm_mujoco.py --language java` 或 `--language kotlin` 并提供 VM 源码、运行时、TLS 库、官方 MuJoCo 3.4.0、编译器、sysroot 清单、构建宿主包和全新的输出位置。夹具从真正的 JVM 语言程序构建闭环控制器，对照原生物理步进，还检查越界指令拒绝和接收端崩溃状态。
