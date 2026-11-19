# Java 与 Kotlin 同步 AOT

Java 和 Kotlin 的默认开发包可将同步应用及其可达类编译为单个 wasm32 core 模块。JDK 21、Kotlin 编译器和 TeaVM 0.13.1 在构建宿主上运行。默认构建要求本现场 WSEA 签署的对应语言内存资格，范围为单线程、EH、`-O3 -g` 与 16 MiB 非移动托管堆。显式选择 `--legacy-mte` 可测量未签署的候选版本。无插装制品、wasm64 和线程仍需独立验收。

按完整提交、平台及语言安装 SDK，默认目录以 `<平台>/<java或kotlin>/development` 为结尾。显式候选构建仍可选择 `synchronous-aot` 组件。通过授权的现场安装会核对 JDK、目标编译器、sysroot 及回收器摘要。

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

### 按操作选择 ROS 导入

每个允许导入的操作传一次 `--ros-operation <目录名称>`。Xmake 写法为 `add_wros_operations("capability.open", "capability.close", "guard.create", "guard.trigger", "guard.take")`。显式列表也限制类型化 Guard 和 Driver 最终能导入的 ROS 操作。编译器链接后检查真正的 Wasm 导入，未用的操作可被消除。运行时仍须满足 VM 的接口可见性、资源授权和提供方策略。

编译器据此生成 `wros.scene.Calls`。点号和下划线分隔的后续词转换为首字母大写，例如 `guard.trigger` 对应 `guardTrigger`。核对所装版本的 `share/abi/ros.json` 可以找到准确的名称、请求、应答、用途及约束。`Calls.abi()` 返回 ABI 值。`Calls(inputCapacity, outputCapacity)` 的实例私有保存能力令牌。`capabilityOpen(byte[] alias)` 打开能力，`capabilityClose()` 关闭。对于 VM 允许零令牌的操作，可以直接使用尚未打开能力的实例。

160 个消息操作的方法签名均为 `(byte[] request, byte[] reply, long[] written)`，返回 VM 状态码。请求内容须遵照各自的 wire schema，空消息传零长度数组，长度输出传一个元素的数组。包装层将请求复制到有界暂存区，只调用一次宿主，成功后发布应答并在返回前清零暂存区。两个权限报告操作查询未支持的整个类别时，状态 95 还可附带标明未支持的页面。查询不存在的精确函数时没有该页面。拒绝时调用方的应答与长度均保持原值。容量不足时 VM 可以只报告所需长度。有序号或效果未知的请求是否重试须由应用判断。两个暂存区的合计配置上限为 16 MiB，实际可用容量还取决于应用对象及其他堆开销。

`examples/java/synchronous-aot/Exchange.java` 和 `examples/kotlin/synchronous-aot/Exchange.kt` 演示不同操作独立授权、参数错误在触发前拒绝、有界结果和事件计数恰为一次。其他协议的字段见 ABI 目录；某个操作可编译导入与特定厂商、设备、提供方的语义验收分别记录。

### 私有线性内存与模块调用

产物只导出 `_start` 函数。编译器要求模块自有一个非共享的 wasm32 线性内存，最大为 4,096 页，并移除 LLD 自动生成的内存导出。GC 堆、栈及暂存消息都留在模块内。构建记录分别保存链接原始产物和最终 Wasm 的摘要。

VM 的六个 `module.call.*` 操作使用另行登记的交换内存。有些消息需要等到后续确认、取消或撤权才能清零。当前同步 JVM 线路没有提供这种交换内存，也没有为 GC 缓冲区提供跨调用租约。即使路由已登记并授权，使用此堆提交消息仍会得到状态 95。

### 需要其他能力的操作

24 种带能力引用的请求提供第四个参数为 `Calls[]` 的重载。按请求中的字段顺序传入已打开的实例，数组中的每个引用和实际存在的可选引用也占一项。原始请求中的能力字段须留零，资源 ID、长度和其余字段按协议填写。包装层先复制请求，按所选 schema 验证字段，只在私有暂存区中填入令牌，随后调用一次 VM。调用方原数组中的占位符始终为零。缺少或多传引用、占位符非零时返回 22；传入已关闭的实例时返回 9。VM 再分别检查每个引用的用途、绑定资源和当前授权。

Schedule 示例使用两个独立授权建立仿真 ROS 时钟和定时器，推进时间后读取定时器错过的周期数，并检查用 guard 代替时钟权限时的拒绝结果。

## 验收并安装本地编译器

将匹配的宿主工具包置于 `$TOOLCHAIN/libexec/wros/jvm/java` 和 `$TOOLCHAIN/libexec/wros/jvm/kotlin`，准备已审阅的 wasm32/EH C 后端发布记录及其规范化摘要。在固定提交源码中运行以下命令。

```sh
python3 tools/wasm/memtag/qualify_jvm.py --toolchain "$TOOLCHAIN" --sysroots "$SYSROOT" \
  --vm "$VM" --c-release "$C_RELEASE" --approved-c-release-sha256 "$C_RELEASE_SHA256" --output "$NEW_WORK"
```

先审阅 `ownership/results.json`，再使用 `wros.sdk.memory.release` 身份签署 `releases.wasm`。测试分别编译两种语言，使 240 个对象及其数组经历回收后仍可遍历，检查近邻标签及已回收对象的五个粒度，并在 VM 开关 MTE 两种情况下运行。声明包含同一 C 后端及两种语言各自的证据。采用 SDK 的 WSEA 流程签署并准备本地现场配置。[本地发布签署](memory-qualification.md)

```sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --language java --platform unitree \
  --prefix "$PREFIX" --site-profile "$SITE_JSON"
SDK="$PREFIX/$SDK_COMMIT/unitree/java/development"
"$SDK/bin/wrjava" --main-class example.Main "$SDK/examples/java/synchronous-aot/Main.java" -o body.wasm
```

Kotlin 选择 `--language kotlin`、`wrkt` 和 `Main.kt`。每次构建都验证 WSEA 选择与完整宿主包。编译现场授权不授予运行时 ROS 权限。
