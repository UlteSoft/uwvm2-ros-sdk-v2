# Install an SDK and build a guest

[中文](../zh/install-xmake.md)

The installer obtains its host tools from their pinned official projects. [Host tools](host-tools.md)

Use Python 3.11 or later and Git on the build host. The native compiler packages target Linux x86-64. Install Xmake to build the example projects. To execute them, provide a local `uwvm2-ros` with the interpreter and LLVM engines enabled. The VM project documents its host prerequisites and the `xmake build uwvm2-ros` target. [Xmake installation](https://xmake.io/guide/quick-start.html) · [VM build instructions](https://github.com/UlteSoft/uwvm2-ros)

## Identify the Linux host ABI

Run the pinned installer in a new directory. The `host` field identifies the native package ABI for the running Python process. `host_selections` lists the languages recorded for that host at the selected revision.

```sh
hostrev=084c206553f46cbe1f421e9c2f9ef5855f128c08
mkdir -p .tmp
export TMPDIR="$PWD/.tmp"
curl -fsSL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$hostrev/install.py" -o install.py
python3 -I -B install.py list --commit "$hostrev" --prefix "$PWD/sdk"
```

Two Cortex-A15 QEMU systems reported `armv7l` and `AT_HWCAP=4176086`. The installer selected `linux-arm` for the armel Python ELF flags `0x05000200` and `linux-armhf` for the armhf flags `0x05000400`. It also checks known ELF interpreters and compares each package’s hardware requirements with the VFP and NEON capabilities available to the process. At this revision `list` passed on five hosts, and x86_64 had published language selections. [Five-host results](../qualification/linux-host-abi-084c2065.json) · [Arm ELF specification](https://github.com/ARM-software/abi-aa/blob/main/aaelf32/aaelf32.rst)

## Build the ABB WAT example on five Linux hosts

This candidate passed GitHub installation on native x86_64 and i686 and on AArch64, ARM soft-float and ARM hard-float userspaces under QEMU System. Copy the example outside the installation prefix. The bundled tools then build it offline and test it with the interpreter and AOT engine. Both 32-bit ARM runs used a Cortex-A15 with VFPv3, D32 and NEON. Disabling VFP on the soft-float system made the installer reject the package because Xmake requires VFP. [Five-host results and four rebuild digests](../qualification/abb-wat-five-hosts-c5053769.json)

```sh
mkdir -p abb-wat-check && cd abb-wat-check
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
rev=c5053769afe1f08d38dbd6ca835ef98abd1df11e
curl -fsSL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$rev/install.py" -o install.py
python3 -I -B install.py install --commit "$rev" --language wat --platform abb --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -I -B -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM
cp -R "$UWVM_ROS_SDK_ROOT/examples/abb/wat" my-project
cd my-project
xmake build
xmake test -j1
```

## Build your first module

The example pins the bootstrap revision and the SDK revision separately. The bootstrap downloads the selected commit’s `install/install.py`. The output records the full SDK commit and absolute installation directory.

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp"
export TMP="$TMPDIR" TEMP="$TMPDIR" XMAKE_TMPDIR="$TMPDIR"
bootstrap=35160a793faaca9ea7de9d6820687288b5373a78
revision=36c098e85098d7ccc26562972af32f47aafe7560
curl -fsSL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$bootstrap/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform generic --language wat --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export WROS_VM="$(command -v uwvm2-ros)"
cp -R "$UWVM_ROS_SDK_ROOT/examples/wat" my-guest
cd my-guest
xmake build
xmake test -j1
xmake run
```

If the VM lives outside `PATH`, set `WROS_VM` to its absolute executable path. `xmake build` produces a Core Wasm module under the project's `build` directory. The two tests invoke separate VM processes, execute the guest-defined `_start` and propagate guest traps or unsuccessful exits. The WAT example queries the host ABI and checks a signed conversion. After installation the compiler, Xmake adapter and examples operate offline.

## Select a release, language and platform

From the directory containing `install.py` and `selection.json`, use `python3 install.py list --commit "$revision"` to print the choices in the selected revision. Use `--commit` followed by its full 40-character lowercase ID to pin a revision. To pin the bootstrap too, use that ID in the raw GitHub URL in place of `main`. `plan` lists the selected repository files and the native program destinations before fetching them.

```sh
REV="$(python3 -c 'import json; print(json.load(open("selection.json"))["commit"])')"
python3 install.py plan --commit "$REV" --platform unitree --language cpp --prefix "$PWD/sdk"
python3 install.py install --commit "$REV" --platform unitree --language cpp --prefix "$PWD/sdk"
```

- `c` installs native `bin/wrc`, C headers and the sixteen WASIp1 profiles.
- `cpp` installs native `bin/wrcc`, independent C++ headers and the sixteen WASIp1 profiles.
- `wat` installs native `bin/wrwat`, the Core Wasm assembler with WasmMTE support.
- `as` installs `bin/wras` and its pinned AssemblyScript compiler packages. It includes the pinned Node.js 22.22.3 executable. An explicit `WROS_NODE` selects another copy of the same executable. [AssemblyScript projects](languages/as.md)
- `js` installs `bin/wrjs`, QuickJS and the private wasm32 C backend it uses to build each Wasm application. [JavaScript projects](languages/js.md)
- `typescript` installs `bin/wrts`, its strict ES2022 TypeScript compiler and the QuickJS backend. It uses the same pinned Node host as AssemblyScript. [TypeScript projects](languages/typescript.md)
- `py` and `python` install CPython for the generic and Unitree platforms. The shared interpreter runs scripts and `wrpy.py` packages external projects. [Python projects](languages/py.md)
- `rust --mode bindings --no-mte` installs the experimental `no_std` Rust crate and project. The adapter uses upstream `rustc` for `wasm32-unknown-unknown` with `panic=abort`, MTE and EH disabled. Provision the target once with `rustup target add wasm32-unknown-unknown`. Use `WROS_RUSTC` to select a particular installed compiler. [Rust target documentation](https://doc.rust-lang.org/rustc/platform-support/wasm32-unknown-unknown.html)

`generic` selects the common scene ABI. `unitree` additionally installs the Go2 read-only low-state contract and an executable example at `examples/unitree/<language>`. It decodes a recorded driver result in guest memory. Live telemetry requires the operator to provide the matching authorized attachment. The selected platform's local guide is at `platform/<platform>/README.md`. [Pinned Unitree provider contract](https://github.com/UlteSoft/wasmros-deployer/blob/69e5e1be8fe3d669af962e5f63c147959ec45ad7/tests/support/unitree_low_state_contract.txt)

The public include roots are `include/u2rosv2/universal/<language>` and `include/u2rosv2/platform/<platform>/<language>`. The directory names are `c`, `c++`, `rust`, `wat`, `as`, `js` and `typescript`. Binary mode fetches the selected public bindings, examples, runtime inputs and required shared decoder. The private C backend for ECMAScript and the JavaScript implementation used by TypeScript live under `libexec`. The editable AssemblyScript and TypeScript upstream trees are selected in source mode.

Choose any other platform ID printed by `install.py list` to install its read-only guest decoder and an Xmake project at `examples/<platform>/<language>`. For example, `--platform agilex` reads the Scout battery management message, while `--platform fourier` reads the Aurora simulator's LCM feedback. The platform guide identifies the input boundary, representation, named fields and immutable upstream sources. The sample program uses constructed inputs and runs offline.

Git object IDs bind the fetched installation files to the selected commit. The installer verifies each LFS payload's size and SHA-256. Each native program uses a single-member USTAR `.tar.xz` with separate compressed and executable hashes. The installer checks the member name, size, executable mode and ELF architecture, stages the selected tree privately, then publishes it under `<prefix>/<commit>/<platform>/<language>/<mode>`. A repeated installation checks the installed files. `selection.json` inside the selection records the installed paths, sizes, modes and hashes.

## Rebuild a compiler from source

For C, C++ and WAT, `--mode source` retrieves the selected compiler's editable source and builds its executable. The script frontends use pinned compiler packages in both modes. Their source selections additionally include their development sources and fixtures. For WAT on Linux x86-64, the default source selection downloads the official Rust 1.98.0 compiler, Cargo and host standard library from the selected SDK commit, together with the locked Cargo workspace. The build verifies the archives and selected member hashes in `src/compilers/wrwat/bootstrap.json` before using them. The installer records the actual executable hash.

```sh
python3 install.py install --commit "$REV" --platform franka --language wat --mode source --prefix "$PWD/sdk"
```

The initial download needs Python 3.11+, Git, HTTPS access to GitHub, and trusted CA certificates. After download the native WAT build can run offline. Supply a GNU/Linux x86-64 host with a working `cc` linker driver in `/usr/bin:/bin`, glibc development startup objects and libraries, libgcc, zlib, and GNU `/usr/bin/strip`. The Rust compiler, its LLVM libraries, GNU-flavor LLD and Cargo come from the selected archives. For a later offline rebuild, run `python3 -I -B "$UWVM_ROS_SDK_ROOT/src/compilers/wrwat/rebuild.py" --output "$PWD/wrwat"` with a new output path. To use an existing matching official toolchain instead, pass `--rust-bin /path/to/rust/bin` at install or rebuild time. An installation with this override omits the three archives. [Official Rust 1.98.0 host distributions](https://static.rust-lang.org/dist/2026-08-20/channel-rust-1.98.0.toml)

For C/C++, provision CMake 3.26 or later, Ninja and a working native LLVM prefix with `bin/clang`, `bin/clang++` and `bin/ld.lld`. The installer builds the vendored native compiler, linker and archiver once, then builds the sixteen WASIp1 profiles from the selected revision. Use `--jobs` to set the C/C++ rebuild parallelism.

```sh
python3 install.py install --commit "$REV" --platform generic --language cpp --mode source \
    --bootstrap /path/to/host-llvm --jobs 4 --prefix "$PWD/sdk"
```

From a source checkout, release maintainers can rebuild just one guest target. Supply the published Clang, LLD and archiver in a toolchain prefix with `bin/{clang,clang++,wasm-ld,llvm-ar,llvm-ranlib,llvm-nm,llvm-config}` and the published Clang 23 headers under `lib/clang/23/include`. The recipe checks the released program and header hashes before compiling. The target receipt records the input source digest, helper tool digests and the selected ABI.

```sh
python3 -I -B src/compilers/cc/rebuild.py --toolchain /path/to/producer \
    --target wasm64 --core 3.0 --eh --mte --no-threads --language cpp \
    --work "$PWD/.tmp/target-build" --prefix "$PWD/.tmp/target-release" --jobs 4
```

For a wasm64 binary release, merge the generated files in `include/sysroot/c/` and `include/sysroot/c++/` into the matching repository directories. Each shared file must match the producer receipts of every profile that uses it. Copy the profile's link inputs from `lib/wasm64-wasip1/<flavor>/` and its `sysroots.json` and `clang-resource-headers.tar.xz` from `share/toolchains/portable/sysroots/wasm64-wasip1/<flavor>/`. Publish the resulting library entries in the native and cross-host distribution catalogs.

## Configure your Xmake target

Include the installed `tools/xmake/ros.lua`. Set the target kind to `binary`, select its language, declare its source files and export a guest-defined `_start`. C and C++ targets can contain multiple translation units, use `add_includedirs`, `add_defines` and `add_wros_exports`. Rust takes one crate root. WAT takes one text module and uses `add_wros_operations` for its exact ROS imports. `set_wros_test_queries("abi")` gives the local test VM the read-only ABI query. A local test with no query requests runs without that grant.

The C-family SDK installs the WASIp1 headers in `include/sysroot/c/`, libc++ and Herbceptions in `include/sysroot/c++/`, and the GNUstep headers for Objective-C selections in `include/sysroot/objc/`. For example, the source for `<stdio.h>` is `include/sysroot/c/stdio.h`, and the source for `<vector>` is `include/sysroot/c++/vector`.

The installer checks each header against the profile's producer receipt, then links it into the multiarch sysroot that Clang uses automatically. It selects `wasi/version.h` from `c/config/mte/` or `c/config/nomte/` and libc++'s `__config_site` from `c++/config/threads/` or `c++/config/single/`. EH profiles also expose the libunwind headers. The static archives and startup objects live under `lib/<triple>/<flavor>/`. The receipt and archive of Clang's built-in resource headers live under `share/toolchains/portable/sysroots/<triple>/<flavor>/`.

C-family targets can use `add_links("wasi-emulated-mman")` to link an optional archive from the selected sysroot. The same project can pass `-lwasi-emulated-mman` when invoking its compiler directly.

AssemblyScript takes one application source and accepts `add_wros_operations("abi")` for a scalar guest or `set_wros_profile({as_driver = true})` for bounded staging. JavaScript and TypeScript use `set_wros_entry` to choose the entry among multiple declared sources. Their backend exports the guest's `_start`. Use `add_wros_operations` to select ROS imports and `set_wros_test_queries("realtime-clock")` to grant QuickJS the real-time clock in the local VM. A generic ABI example requests both `"abi"` and `"realtime-clock"`.

```lua
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("controller")
    set_kind("binary")
    set_language("cpp")
    set_ros_platform("generic")
    set_wros_profile({abi = "wasm32", core = "3.0", memory64 = true,
                      mte = true, eh = true, threads = false, std = "c++20"})
    add_files("controller.cpp")
    set_wros_test_queries("abi")
    add_wros_tests("int", "aot")
target_end()
```

The native profiles default to Core 3, a wasm32 language ABI, the memory64 feature enabled in the VM, synchronous MTE, EH enabled and threads disabled. C++ additionally defaults to Herbceptions. Use `abi` for a language's pointer width and `memory64` for the VM feature. WAT specifies its memory type in the module itself, so its assembler uses the memory64 setting for validation. `wrc` and `wrcc` select their sysroot using `--target wasm32` (default) or `--target wasm64`. Both ship Core 3, static single-threaded libraries, EH and MTE under `lib/<triple>/core3.0-eh-mte`. Other profiles require matching build inputs.

On wasm32, C/C++ pointers and the primary linear memory are 32-bit with either VM memory64 setting. On wasm64, pointers, `size_t` and primary linear memory addresses are 64-bit. This LLVM backend requires `--memory64` for wasm64 and rejects `--target wasm64 --no-memory64`. This target uses UWVM's Preview 1 extension with `*_wasm64` imports under `wasi_snapshot_preview1`. Deployment requires a VM that implements the extension and grants the application's imports.
