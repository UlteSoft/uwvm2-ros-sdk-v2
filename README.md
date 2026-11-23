# WROS SDK v2

[简体中文](README.zh.md)

WROS SDK v2 builds Core WebAssembly guests for uwvm2-ros. The Linux x86-64 installer selects the language and platform at an immutable Git revision. [Language coverage](document/en/language-coverage.md) · [Platform coverage](platform/README.md)

## Install from the current main revision

Start in an empty project directory. This command pins both installer stages to the same published SDK revision. The installer builds the VM from its pinned official source. Five-host INT and AOT qualification is pending.

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp"
revision=$(git ls-remote --exit-code https://github.com/UlteSoft/uwvm2-ros-sdk-v2.git refs/heads/main | cut -f1)
curl -fsSL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform generic --language c --prefix "$PWD/sdk"
```

## Binary distribution

Only WROS-built artifacts that incorporate SDK source changes belong in `bin/`. For each such artifact, keep its upstream revision, local changes and rebuild inputs in `src/`. Fetch unmodified tools, libraries and bootstrap components from their pinned official distributions and verify the digests before use. Keep downloaded inputs in the installation cache. The current runtime requalification records the VM revision and host executable for each matrix. [Host dependencies](document/en/host-tools.md) · [Runtime qualification](document/qualification/runtime-qualification.json)

## Run the historical Franka installation

The pinned examples below reproduce earlier SDK revisions. Current release acceptance uses the VM commit and executable hashes in the runtime qualification record.

Start in a new directory with Python 3.11+, Git and curl. The selected Linux x86-64 host needs glibc 2.38+ and the system libgcc and libatomic runtime libraries. This Franka example reads five two-element Elbow fields through the public C interface. The two Xmake tests run the compiled Wasm with the installed interpreter and LLVM AOT engine.

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
revision=1259ec5215d7296118c1d4bdd4f1e739839adc2e
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform franka --language c --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
cp -R "$UWVM_ROS_SDK_ROOT/examples/franka/c" my-guest
cd my-guest
wrc main.c --reactor --export _start -g -o direct.wasm
xmake build
xmake test -j1
```

The GitHub install and both offline project builds ran with empty HOME and caches inside separate namespaces and a shared 64 GiB zero-swap cgroup. The executable traces identify Xmake and uwvm2-ros inside the selected prefix. [Qualification record](document/qualification/franka-1259ec52.json) · [Host sources and build prerequisites](document/en/host-tools.md)

To build ABB ROS 1 with the same bundled tools, select platform `abb` and language `c`, `cpp` or `rust`. Copy `examples/abb/c/ros1`, `examples/abb/cpp/ros1` or `examples/abb/rust/ros1` from that selection and run the same Xmake commands. All three installed compilers produced real Wasm and passed the 140 independent genpy wire cases on both engines. Rust requires glibc 2.39+ and libstdc++ with GLIBCXX_3.4.32. [Independent ABI and guest results](document/qualification/abb-1259ec52.json)

## Build an ABB ROS 1 project with standard Go or TinyGo

Start in an empty project directory. The default below selects standard Go. To use TinyGo, change `language=go` to `language=tinygo` and run the same commands in another directory. The example calls the VM scene ABI and encodes and decodes a RAPID request and an EGM state array with a Header.

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
revision=a5863c63842081570e8541fc037b43fcc52506fd
language=go
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --language "$language" --platform abb --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
cp -R "$UWVM_ROS_SDK_ROOT/examples/abb/$language" abb-guest
cd abb-guest
case "$language" in
    go) wrgo . -o direct.wasm ;;
    tinygo) wrtg . -o direct.wasm ;;
esac
xmake build
xmake test -j1
```

The installation pins the standard Go release with the verified offline host rebuild. TinyGo can also use this revision for the distributed example. The independently qualified 140-vector TinyGo source and binary installations are recorded separately. [Corrected Go build](document/qualification/abb-a5863c63.json) · [Both toolchains and wire-format results](document/qualification/abb-28466433.json)

## Unitree Python and Franka Go toolchains

The Unitree Python guide pins a public installation of CPython 3.14.8. Both documented binary selectors run an external Python program inside the shipped Wasm interpreter under INT and LLVM AOT. The Franka Go guide pins the separate release tested with the standard Go and TinyGo compilers. [Unitree Python commands](document/en/languages/py.md) · [Franka Go and TinyGo commands](include/u2rosv2/platform/franka/go/README.md) · [Qualification by revision](document/en/qualification.md)

## Earlier ABB C++ candidate

Use a Linux x86-64 host with Python 3.11+, Git and Xmake. Put a compatible INT/AOT build of uwvm2-ros on PATH to execute the Wasm. Run the following in your own project directory.

The following example downloads the standalone installer, selects the ABB C++ candidate, and builds the ROS 1 service and system-state example in a separate project directory.

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp"
export TMP="$TMPDIR" TEMP="$TMPDIR" XMAKE_TMPDIR="$TMPDIR"
revision=947c3067ff00cd48f3a58de9abbecec4710df69a
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --language cpp --platform abb --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export WROS_VM="$(command -v uwvm2-ros)"
cp -R "$UWVM_ROS_SDK_ROOT/examples/abb/cpp/ros1" my-guest
cd my-guest
"$UWVM_ROS_SDK_ROOT/bin/wrcc" main.cpp --reactor --export _start -g -o direct.wasm
xmake build
xmake test -j1
```

Use `--language c` for the C headers and `wrc`. Use `--language wat` for the assembler. The source tree contains wasm32 and wasm64 WASIp1 libraries for the Core 3.0, EH, single-threaded WasmMTE configuration. Configuration support and runtime qualification depend on the selected compiler and target.

The common bindings live in `include/u2rosv2/universal/<language>`. All 36 dedicated platforms have C, C++, Rust, AssemblyScript, JavaScript, TypeScript and WAT interfaces under `include/u2rosv2/platform/<platform>`. ABB, Franka and Unitree also provide Go modules for both standard Go and TinyGo. Each platform guide lists the messages and fields its bindings cover. Select `generic` for the common ABI alone. The C++ directory is named `c++` and its installer ID is `cpp`. [Public bindings](include/u2rosv2/) · [Platform guides](platform/README.md)

## Install standard Go or TinyGo

For ABB ROS 1, select `--platform abb` and `--language go` or `--language tinygo` from a revision containing the ABB Go module. The guide builds an external guest that exchanges a RAPID service request and reads EGM channel state. [ABB Go installation and domain packages](include/u2rosv2/platform/abb/go/README.md)

For Unitree, start in a new project directory at public commit `b92c100dcb2586846797eb40ddb357764b1cd26e`. Each guide includes the root installer, direct compiler and Xmake commands for its toolchain. Both installations supply Xmake and the VM. [wrgo](document/en/languages/go.md) · [wrtg](document/en/languages/tinygo.md) · [Unitree](document/qualification/unitree-b92c100d.json)

The Python selection supplies `wrpy.py`, the shared CPython 3.14.8 Wasm command and the target static library. Unitree adds 43 ROS message classes with plain XCDR1 codecs. The installed interpreter ran external scripts and the packaged Unitree project in both engines. Starting a script by guest pathname failed with default MTE. [Python and Unitree projects](document/en/languages/py.md)

## Compilers under review

Standard Go 1.24.2 (`wrgo`) and TinyGo 0.38.0 (`wrtg`) share the common Go package and the selected ABB, Franka or Unitree message package. Each toolchain has its own build and guest execution tests. For the current 32-bit Wasm linear memory target, Go pointers are 64 bits with standard Go and 32 bits with TinyGo. Language totals count Go once. WAT has its own assembler, `wrwat`. The C interoperability bridge is qualified with each language project that uses it. [Standard Go](document/en/languages/go.md) · [TinyGo](document/en/languages/tinygo.md) · [Legacy selection coverage](document/en/language-coverage.md)

The review tree contains the native `wrrs` sources based on Rust 1.98.0. Release archives and qualified target combinations are tracked by frozen revision. [Rust source and local changes](src/compilers/rust/README.md) · [Qualification by revision](document/en/qualification.md)

## Source and evidence

- [Installation and Xmake](document/en/install-xmake.md)
- [37 platform selections and their read-only interfaces](platform/README.md)
- [Compiler sources and build recipes](src/compilers/)
- [WebAssembly libraries](lib/)
- [C headers](include/u2rosv2/universal/c/uwrosv2/scene.h), [C++ headers](include/u2rosv2/universal/c++/uwrosv2/scene.hpp), [Rust crate](include/u2rosv2/universal/rust/uwrosv2/Cargo.toml)
- [VM contract](src/abi/contract.json) and [independent import and authorization results](document/qualification/bindings.json)
- [ROS porting cohort and pinned archive digests](src/qualification/corpus/selection.json)
- [Qualification by revision](document/en/qualification.md)
- [Language selections and migration status](document/en/language-coverage.md)
