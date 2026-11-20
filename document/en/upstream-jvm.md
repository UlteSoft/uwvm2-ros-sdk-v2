# Upstream JVM library tests

Run the upstream replay with a signed Java site and a signed Kotlin site that match the SDK revision, C backend and VM. The [JVM qualification instructions](jvm.md) describe how to prepare those sites. The runner builds through the installed SDK on Linux x86-64 and runs on the supplied VM. It uses the Unitree SDK platform selection and the wasm32, Core 3.0, single-threaded, EH, synchronous MTE, -O3 and -g profile.

Set the VM, Xmake and site paths to the exact inputs approved for the run. Use the host's existing serial qualification gate for a 64 GiB cgroup with swap disabled. The output directory must be new.

    "$QUALIFICATION_GATE" python3 -B tests/upstream_jvm_libraries.py \
      --repository "$PWD" --commit "$(git rev-parse HEAD)" \
      --vm "$VM" --xmake "$XMAKE" \
      --java-site "$JAVA_SITE" --kotlin-site "$KOTLIN_SITE" \
      --output "$OUTPUT"

The runner retrieves four exact source files from GitHub and verifies their SHA-256 digests before building. For an offline run, add --sources and supply a directory containing fastutil/HashCommon.java, fastutil/HashCommonTest.java, kotlin/_Ranges.kt and kotlin/CoercionTest.kt. The same digest checks apply to the cached files.

Java replays fastutil 8.5.16's hash inverse case. The harness keeps the four mix and inverse methods and the upstream test body intact, and supplies a scalar assertion adapter. Kotlin replays twelve primitive coercion expectations from Kotlin 2.1.20. The harness relocates six methods from the standard library package and adapts the assertions to direct checks. The suite verifies the selected methods and test cases. Full library builds require additional JVM standard library and test-framework support.

Results record checked source digests, the VM digest, actual imports, product digests and logs from both engines. The controls verify that hiding the ROS ABI denies guest instantiation. Xmake builds and executes the same cases through the installed project rules.

Run tests/jvm_raw_bits.py with --repository, --commit, --vm, --site and --output to verify Java's exact float, double and integer bit operations. Use the Java site for --site. The check runs on the pinned JDK and on both VM engines. It also exercises fastutil's unmodified nextPowerOfTwo method bodies and submits the full class to the closed compiler to record its first unsupported dependency.
