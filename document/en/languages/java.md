# Build a Java guest

Select `--language java --platform abb` for the ABB ROS 1 readers. Select `--platform generic` for the scene API. The SDK publishes a native `wrjava` launcher for Linux x86-64, i686, AArch64, ARM soft-float and ARM hard-float. The prebuilt WROS TeaVM driver and runtime classes are awaiting publication. Use the explicit source rebuild below. It obtains the matching JDK from Eclipse Temurin on x86-64 and Debian Snapshot on the other four hosts. The Debian hosts require `dpkg-deb` and the system libraries for their JRE. The complete workflow also needs the matching WROS C compiler, Xmake and VM. Independent installation, execution and deployer qualification are pending.

Use the full release commit for REV. From a checkout, the local Git materializer accepts the same immutable revision. Both installers report the actual SDK directory. Python 3.11 or newer is required.

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
python3 -I -B install.py rebuild --commit "$REV" --platform abb --language java --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
cp -R "$UWVM_ROS_SDK_ROOT/examples/abb/java" abb-java
cd abb-java
wrjava --main-class example.Guest --source-root src --keep-work build-inputs -o abb-state.wasm
xmake build
xmake test -j1
```

For a local frozen Git revision use `python3 -I -B install/install.py "$PWD" "$REV" "$PWD/sdk" rebuild --language java --platform abb`. Both installers fetch the selected JDK and the 29 compiler JARs using the official release and Maven Central URLs recorded in the SDK. Each download is checked against its locked size and SHA-256. To supply the Java inputs from a cache, place each file at `<prefix>/.cache/sha256/<sha256>` along with the required Git LFS objects. Guest builds use the installed JDK, JARs, native compiler and headers locally. [Temurin lock](../../../src/compilers/jvm/openjdk/upstream.json) · [Debian lock](../../../src/compilers/jvm/openjdk/debian/upstream.json) · [Compiler JAR lock](../../../src/compilers/jvm/java-jars.json)

Use `set_wros_main_class("your.package.Main")` and declare each application source with `add_files` in Xmake. On the command line, pass individual .java files, repeated `--source-root` directories or both. `--keep-work` requires a new directory and retains JVM bytecode in `classes` and TeaVM's generated C in `generated`. `-O0` through `-O3`, `-Os`, `-Oz` and `-g` configure the final C compile and link. The ABI is wasm32 with Core 3.0, memory64 feature enabled, EH, MTE and a single thread.

`u2rosv2.Scene` exposes ABI discovery, capability open and close, and a clock read into a caller-owned byte array. Capability operations require matching deployment grants. The ABB project reads 14 ROS 1 message and service-body types and can replay its fixture-only entry on the host JVM using the installed JDK. [Scene bindings](../../../include/u2rosv2/universal/java/src/u2rosv2/Scene.java) · [ABB types and replay](../../../include/u2rosv2/platform/abb/java/README.md)

The rebuild compiles the WROS TeaVM classes with the selected JDK, rebuilds the launcher with the host C11 compiler (`CC`, default `cc`), includes the TeaVM and OpenJDK sources, and fetches 11 external source JARs from Maven Central. On Debian JDK hosts it restores the matching source package from the same Debian Snapshot. Upstream distribution rebuilds and Java standard-library qualification are pending. [Source and package reproduction](../../../src/compilers/jvm/README.md)
