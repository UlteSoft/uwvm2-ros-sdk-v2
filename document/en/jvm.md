# Synchronous Java and Kotlin AOT

The optional `synchronous-aot` component compiles an application’s JVM classes and their reachable class-library code to a single wasm32 core module. The host runs JDK 21, the Kotlin frontend when selected, and TeaVM 0.13.1. The guest runs on uwvm2-ros. This component has no signed managed-neighbor release. The compiler requires an explicit `--legacy-mte` and enables WasmMTE in the compiler and guest allocator. Default development selection, default strict compilation, MTE-off, wasm64 and pthreads are unavailable for these languages.

Install one platform and language at a full SDK commit. Use the fixed bootstrap invocation in the installation guide and pass `--component synchronous-aot` after the bootstrap’s `--`. The installed path ends in `<platform>/<java-or-kotlin>/synchronous-aot`. The selected package contains its language frontend and Xmake adapter, the shared guarded runtime sources, pinned host identities, examples and this guide. Verify the existing Linux x86-64 SDK1 JVM build-host bundle with the selected `language/<language>/host-inputs.json`. Only named JARs enter the compiler classpath. Java excludes the Kotlin compiler and runtime JARs. LLVM and the independently matched strong-MTE sysroot are supplied by the developer.

Prepare a build-host bundle from Ubuntu OpenJDK 21.0.10+7-Ubuntu-125.10, matching system libraries and the selected Maven inputs. The helper reads a local Maven cache or an optional flat `--jars DIR`. Add `--fetch-missing-jars` to fetch only missing entries in this language’s pinned manifest. Every byte is checked before the new directory is published. The Linux x86-64 JDK and system library paths below apply to the qualified host.

```sh
python3 "$UWVM_ROS_SDK_ROOT/language/jvm/prepare_host.py" java \
  --jdk /usr/lib/jvm/java-21-openjdk-amd64 --system-libs /usr/lib/x86_64-linux-gnu \
  --fetch-missing-jars --output "$BUILD_DIR/java-host"
export WROS_JVM_BUNDLE="$BUILD_DIR/java-host"
```

Select `kotlin` to provision the Kotlin compiler. Java requires 29 pinned JARs and Kotlin requires 36. An installed compiler bundle can also supply the `--jdk`, `--system-libs` and `--jars` inputs offline.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrjava" --legacy-mte --main-class example.Main \
  --toolchain "$WROS_TOOLCHAIN" --sysroots "$WROS_SYSROOTS" --bundle "$WROS_JVM_BUNDLE" \
  --work "$BUILD_DIR/java-log" -o "$BUILD_DIR/body.wasm" Main.java
```

Kotlin uses `wrkt` and `.kt` sources. `--main-class` selects the JVM class containing `static void main(String[])`. Kotlin can name the class with `@file:JvmName("Main")`. Optional `--work` keeps command logs, hashes and final imports in a new directory. Compilation fixes `-O3 -g`, single-thread Core 3.0, the wasm32 EH sysroot, 16 MiB of Java allocations and 256 MiB maximum linear memory. Application bytecode goes through a closed call and instruction check before TeaVM. The ELF host compiler never becomes a guest artifact.

Use `examples/<language>/synchronous-aot/xmake.lua` with `UWVM_ROS_SDK_ROOT` pointing at the selected install and the three build-input variables above. `set_wros_jvm_main("example.Main")` names the entry class, `set_language` selects the frontend and `add_files` selects source. The entry declaration applies to JVM applications. Xmake requires `set_optimize("fastest")`, `set_symbols("debug")`, `mte = "legacy"`, Core 3.0 and the single-thread EH profile.

The included samples use `wros.scene.Scene.abi()` and the explicitly granted guard operations. `Guard.open(byte[])`, `create()`, `trigger()`, `take(long[])` and `close()` return the VM status. The output array for take contains one word. A guard needs capability open/close plus guard create/trigger/take and the matching scene grant. No handles transfer implicitly. The guest may use independently granted realtime and monotonic clocks through WASIp1’s read-only clock call.

The accepted application bytecode covers local classes, primitive arithmetic and arrays, explicit GC, scene ABI and guard calls, and the clock methods. The verifier rejects other external calls, native methods, dynamic call sites, monitors and catch handlers; unhandled exceptions end the guest. Reflection, arbitrary class libraries, direct buffers, JNI, file/network I/O and threads require additional implementation. This scoped component supplies neither safety certification nor a deployable signed release.

The pinned build-host JVM runs interpreted with core dumps disabled. The guest always goes through the optimized Wasm AOT compiler.

### Isolated driver sessions

`wros.scene.Driver` attaches to a deployment-provisioned alias. `open(byte[] alias, int requestLimit, int responseLimit)` takes limits between zero and 65,536 bytes. Set the response limit at least as high as the deployment's registered maximum. Call `connect()`, then `submit(long sequence, long deadline, byte[] payload)` with the canonical payload for the registered schema and an absolute monotonic deadline. Modules receive each operation and the matching resource grant from the VM.

`result(long sequence, byte[] payload, long[] outcome)` requires a destination at least as large as the selected response limit and two outcome words. A successful call stores the driver status, the number of bytes received, and that many payload bytes. A rejected call preserves the caller's arrays. The method returns the VM operation status independently from the driver's status. `describe(long[4])` returns phase, sequence, status and the unknown-effect bit. Call `disconnect()` to detach the transport and `close()` to release the local capability. Provider lifetime and TLS identity belong to the deployment. The wrapper clears its own message staging buffers after use.

Run `tests/jvm_mujoco.py --language java` or `--language kotlin` with the VM source, runtime, TLS library, official MuJoCo 3.4.0, compiler prefix, sysroot manifest, build host bundle and an empty output location. The fixture builds a closed-loop controller from actual JVM language source, compares native motion with the Wasm controller and checks the receiver's range rejection and crash diagnostics.

### Selecting ROS operations

Pass `--ros-operation <catalogue-name>` once for each permitted ROS import. In Xmake use `add_wros_operations("capability.open", "capability.close", "guard.create", "guard.trigger", "guard.take")`. An explicit list also limits imports emitted by the typed Guard and Driver APIs. The compiler checks actual Wasm imports after linking. It omits unused operations. ROS interface visibility, resource grants and provider policy are then enforced by the VM.

The compiler generates `wros.scene.Calls` for the selected names. Dots and underscores become camel-case word boundaries, so `guard.trigger` maps to `guardTrigger`. Consult `share/abi/ros.json` for the exact registered name, wire request, result, purpose and contract. `Calls.abi()` returns the ABI value. A `Calls(inputCapacity, outputCapacity)` instance stores its capability privately. `capabilityOpen(byte[] alias)` obtains the handle. `capabilityClose()` releases it. An unopened instance can perform an operation that the VM permits with token zero.

Each of the 160 message operations takes `(byte[] request, byte[] reply, long[] written)` and returns the VM status. Use the operation's canonical wire schema. Use zero-length arrays for empty messages and a one-element array for the reply length. The frame owns bounded scratch, copies the request, invokes the host once, publishes a successful reply and wipes its scratch on return. The two permission-report operations can also return status 95 with a page identifying an unsupported family. An unknown exact function supplies no page. A denied call preserves both caller outputs. A size error can publish the required capacity without copying reply bytes. Keep a sequenced or effect-unknown operation under explicit application control when deciding to retry. The two configured scratch capacities together are limited to 16 MiB; the guest heap also contains the application, objects and metadata. Its available capacity can be smaller.

`examples/java/synchronous-aot/Exchange.java` and `examples/kotlin/synchronous-aot/Exchange.kt` show independent operation grants, malformed arguments refused before a trigger, a bounded reply and the observed single event. The ABI catalogue describes the remaining protocols. Compiler admission for an operation documents the transport surface, separately from device- and provider-specific semantic qualification.

### Guest memory and module calls

The guest publishes only its `_start` function. The compiler verifies that the final module owns a single unshared wasm32 linear memory with a maximum of 4,096 pages, and removes LLD's implicit export of that memory. This keeps the GC heap, stack and temporary message buffers private. The build receipt records both the original linker output digest and the published Wasm digest.

The VM's six `module.call.*` operations use an independently registered exchange memory. A receiver may have to erase an outstanding message after a later acknowledgement, cancellation or revocation. The synchronous JVM profile does not provide such a memory or a lease for a GC buffer. A registered and authorized route therefore returns status 95 for a submission from this heap. Dropping the privacy of the regular heap would invalidate that isolation contract.
