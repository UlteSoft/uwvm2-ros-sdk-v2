# Synchronous Java and Kotlin AOT

The optional `synchronous-aot` component compiles an application’s JVM classes and their reachable class-library code to a single wasm32 core module. The host runs JDK 21, the Kotlin frontend when selected, and TeaVM 0.13.1. The guest runs on uwvm2-ros. This component has no signed managed-neighbor release. The compiler requires an explicit `--legacy-mte` and enables WasmMTE in the compiler and guest allocator. Default development selection, default strict compilation, MTE-off, wasm64 and pthreads are unavailable for these languages.

Install one platform and language at a full SDK commit. Use the fixed bootstrap invocation in the installation guide and pass `--component synchronous-aot` after the bootstrap’s `--`. The installed path ends in `<platform>/<java-or-kotlin>/synchronous-aot`. The selected package contains its language frontend and Xmake adapter, the shared guarded runtime sources, pinned host identities, examples and this guide. Verify the existing Linux x86-64 SDK1 JVM build-host bundle with the selected `language/<language>/host-inputs.json`. Only named JARs enter the compiler classpath. Java excludes the Kotlin compiler and runtime JARs. LLVM and the independently matched strong-MTE sysroot are supplied by the developer.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrjava" --legacy-mte --main-class example.Main \
  --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --bundle "$WROS_JVM_BUNDLE" \
  --work "$BUILD_DIR/java-log" -o "$BUILD_DIR/body.wasm" Main.java
```

Kotlin uses `wrkotlin` and `.kt` sources. `--main-class` selects the JVM class containing `static void main(String[])`. Kotlin can name the class with `@file:JvmName("Main")`. Optional `--work` keeps command logs, hashes and final imports in a new directory. Compilation fixes `-O3 -g`, single-thread Core 3.0, the wasm32 EH sysroot, 16 MiB of Java allocations and 256 MiB maximum linear memory. Application bytecode goes through a closed call and instruction check before TeaVM. The ELF host compiler never becomes a guest artifact.

Use `examples/<language>/synchronous-aot/xmake.lua` with `UWVM_ROS_SDK_ROOT` pointing at the selected install and the three build-input variables above. `set_wros_jvm_main("example.Main")` names the entry class, `set_language` selects the frontend and `add_files` selects source. The entry declaration applies to JVM applications. Xmake requires `set_optimize("fastest")`, `set_symbols("debug")`, `mte = "legacy"`, Core 3.0 and the single-thread EH profile.

The included samples use `wros.scene.Scene.abi()` and the explicitly granted guard operations. `Guard.open(byte[])`, `create()`, `trigger()`, `take(long[])` and `close()` return the VM status. The output array for take contains one word. A guard needs capability open/close plus guard create/trigger/take and the matching scene grant. No handles transfer implicitly. The guest may use independently granted realtime and monotonic clocks through WASIp1’s read-only clock call.

The accepted application bytecode covers local classes, primitive arithmetic and arrays, explicit GC, scene ABI and guard calls, and the clock methods. The verifier rejects other external calls, native methods, dynamic call sites, monitors and catch handlers; unhandled exceptions end the guest. Reflection, arbitrary class libraries, direct buffers, JNI, file/network I/O and threads require additional implementation. This scoped component supplies neither safety certification nor a deployable signed release.
