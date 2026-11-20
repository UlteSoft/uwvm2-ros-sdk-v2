# JVM 上游库测试

运行测试需要 Java 和 Kotlin 各自的签名站点。站点必须与所选 SDK 修订、C 后端和 VM 匹配。配置步骤见 [JVM 资格验证](jvm.md)。运行器通过 Linux x86-64 上安装的 SDK 生成 Wasm 并交给指定 VM 执行。测试采用 Unitree SDK 平台、wasm32、Core 3.0、单线程、EH、同步 MTE、-O3 和 -g。

为本次运行设置已获批准的 VM、Xmake 和站点路径。通过宿主现有的串行测试入口，在关闭 swap 的 64 GiB cgroup 下执行。输出目录必须是新目录。

    "$QUALIFICATION_GATE" python3 -B tests/upstream_jvm_libraries.py \
      --repository "$PWD" --commit "$(git rev-parse HEAD)" \
      --vm "$VM" --xmake "$XMAKE" \
      --java-site "$JAVA_SITE" --kotlin-site "$KOTLIN_SITE" \
      --output "$OUTPUT"

运行器从 GitHub 获取四个固定提交中的源码文件，构建前检查其 SHA-256。离线运行时可用 --sources 指定缓存目录，目录中须包含 fastutil/HashCommon.java、fastutil/HashCommonTest.java、kotlin/_Ranges.kt 和 kotlin/CoercionTest.kt。同样会校验缓存文件的摘要。

Java 重放 fastutil 8.5.16 的哈希逆变换测试。适配代码完整保留四个哈希与逆变换方法、上游测试方法体，并提供标量断言。Kotlin 重放 Kotlin 2.1.20 的十二项原始数值边界断言。适配代码迁移了六个标准库方法的包名，将断言转换成直接检查。测试覆盖这些方法和用例。完整库构建仍需要更多 JVM 标准库与测试框架支持。

结果记录已校验的源码摘要、VM 摘要、实际导入、产物摘要以及两个引擎的测试日志。权限对照用例验证隐藏 ROS ABI 后实例化会被拒绝。Xmake 通过已安装的项目规则来构建和执行相同的用例。

验证 Java 的浮点与整数位操作时，可用 --repository、--commit、--vm、--site 和 --output 运行 tests/jvm_raw_bits.py。其中 --site 使用 Java 站点。测试会使用固定 JDK 和两个 VM 引擎，执行 fastutil 原样的 nextPowerOfTwo 方法体，并将完整类交给受限编译器，记录首个未获准的依赖。
