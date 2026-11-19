# WROS SDK developer guide

[C++ typed error returns with wrcc](cpp.md)

[Nim application development](nim.md)

[Migrate ROS package resources](migration.md)


[WasmMTE detection guarantees](memtag.md)
- [Qualify and sign a local memory-tagging toolchain](memory-qualification.md)

For driver/model security and the division between Wasm and deployment authority,
read [Local driver and model attachments](local-attachments.md).

[Build and run a Wasm project with xmake](xmake.md) · [Xmake API index](xmake-api-index.md)

## Compiler command names

The public compiler name uses `wr` followed by the language abbreviation. Use the language ID with the installer and Xmake. Run the command from the selected installation’s `bin` directory.

| Language | Installation ID | Command |
| --- | --- | --- |
| C | `c` | `wrc` |
| C++ | `cpp` | `wrcc` |
| Objective-C | `objectc` | `wrobjc` |
| Fortran | `fortran` | `wrf` |
| Rust | `rs` | `wrrs` |
| TinyGo | `tinygo` | `wrtg` |
| Nim | `nim` | `wrnim` |
| Lua | `lua` | `wrlua` |
| [JavaScript](js.md) | `js` | `wrjs` |
| [D BetterC](d.md) | `d` | `wrd` |
| Java | `java` | `wrjava` |
| Kotlin | `kotlin` | `wrkt` |
| C# | `csharp` | `wrcs` |
| [F#](fsharp.md) | `fsharp` | `wrfs` |
| [Visual Basic](vbnet.md) | `vbnet` | `wrvb` |

Java and Kotlin install their synchronous AOT frontend by default and accept an approved local site. The default C# installation compiles freestanding integer methods. The full CLR development package is pending. [C# compiler guide](csharp.md) Check `revision-help` at the selected commit for the command and use `plan` to check package availability. The archive utility is `wrar`. Previous installations retain the names from their pinned commit.

## Install a pinned selection

Run the trusted bootstrap with Python 3.11 or newer. The commit argument is the full 40-character Git object ID. Use the same bootstrap with later SDK commits that implement the installation contract. The default source is the official public SDK repository. A trusted local Git repository works offline.


On a new machine, fetch the initial bootstrap as a single file. Set `REV` to the full commit you want to install. The bootstrap itself also works outside a checkout.

```sh
curl --fail --silent --show-error --output bootstrap.py \
  https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/cf09b4b30e3801deb73c012957b9f1c5f1196289/install/bootstrap.py
printf '%s  %s\n' e93d8e7c2fe733d8c33ca09c5dfee38d5047b0c11ba0524b5b2d8fecb36f1f29 bootstrap.py | sha256sum --check -
python3 bootstrap.py revision-help --commit "$REV" --language cpp --platform unitree
```

```sh
python3 install/bootstrap.py plan --commit "$REV" --language cpp --platform unitree
python3 install/bootstrap.py install --commit "$REV" --language cpp --platform unitree --prefix "$SDK_HOME"
python3 install/bootstrap.py revision-help --commit "$REV" --language cpp --platform unitree
```

The bootstrap requests the selected revision's small Python hook and package manifests. It fetches payload files individually, verifies SHA-256 and length, and publishes the complete selection by directory rename. Shared payloads use a digest cache. A revision hook is executable code from the selected commit. Select a trusted commit and run as the developing user. For offline use add `--local-repository /path/to/sdk`. The `requested_paths` field lists every Git object path requested by the bootstrap.

The stable operations are `plan`, `install` and `revision-help`. Pass revision-specific options after `--`. Select `--component protocol` for the language-neutral contract and platform source references, or `--component compiler-source` to install the shared Wasm LLVM backend and sysroot build inputs alongside the selected language. C, C++, Fortran, Lua, Objective-C, Rust and TinyGo use this backend. The package includes the pinned backend source archives and patches. Language-specific compiler and runtime prerequisites are documented in each language guide. The ordinary development selection excludes those archives. The minimum Python version also applies to the preinstalled bootstrap.

For an existing compiler integration, pass `-- --component bindings` to install only the selected raw declarations, the licence, and the selected language and platform metadata. C and C++ share a header. This revision also publishes Rust and AssemblyScript declarations. This component fetches no compiler, compiler sources or full ABI catalogue. The original bootstrap can discover it with `revision-help` at this commit.


For D, select `--language d -- --component bindings`. The installation includes `language/d/wros_scene.d`, its C import adapters and the ROSv2 header. A D module can use `import wros_scene : wros_abi;` and call `wros_abi()`. Each i32 and i64 operand maps to D uint and ulong respectively. The raw component supplies declarations for all 163 common operations. The [BetterC qualification fixture](../../tests/d_bindings/qualify.py) runs a wasm32 application against the VM with and without its ABI grant. The [D development selection](d.md) includes a signed-site BetterC compiler and Xmake adapter for single-threaded wasm32. Full DRuntime and garbage collection still need qualification.

### Build a Nim Wasm application from a public installation

This example pins the public SDK revision exercised by the clean-install test. Supply the signed Nim site profile distributed by your operator. It identifies the approved host compiler, target sysroot and release for the selected VM. Python 3.11 or later is required.

```sh
REV=f8349b2666c8dd97957e94afe50c547f232a5249
curl --fail --silent --show-error "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$REV/install/bootstrap.py" | python3 -I -B - install --commit "$REV" --platform unitree --language nim --site-profile /etc/wros/nim-site.json
SDK="$HOME/.local/share/wros-sdk/$REV/unitree/nim/development"
"$SDK/bin/wrnim" "$SDK/examples/nim/body.nim" --build-receipt -o robot.wasm
```

The installer fetched 53 files for this selection in an empty cache. The installed Xmake adapter also built the application for both VM engines. The program queries the ROS ABI, so the host must expose `uwvm_ros_v2.abi` to the module for it to run. The same receipt was checked against the VM before execution. [Nim compiler and supported profile](nim.md) · [Xmake configuration](xmake.md)


### One-command Unitree installation

In Bash, set `REV` to a trusted 40-character SDK commit. This command downloads the installer and selected files directly from the official repository.

```sh
set -o pipefail
curl --fail --silent --show-error \
  "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$REV/install/bootstrap.py" | \
  python3 -I -B - install --commit "$REV" --platform unitree --language fortran
```

The result’s `directory` field gives the location of `bin/wrc` (C), `bin/wrcc` (C++), `bin/wrf` (Fortran), and `bin/wrar` (archives). Language sources and Xmake platform files are specific to Fortran and Unitree. After a network interruption, repeat the command using the same prefix to reuse verified objects.

For development, supply the paths to the host’s reviewed compiler prefix (`PRODUCER`) and matching sysroot manifest (`RECEIPT`). The wrappers validate the selected build inputs. The default memory-tagged profile also requires the operator’s signed qualification for those inputs and options. Provision the toolchain, sysroot and VM separately. [Host tools and local qualification](fortran.md)

```sh
sdk="$HOME/.local/share/wros-sdk/$REV/unitree/fortran/development"
"$sdk/bin/wrc" --toolchain "$PRODUCER" --sysroots "$RECEIPT" --target wasm32 -O3 -g body.c -o body.wasm
"$sdk/bin/wrf" --toolchain "$PRODUCER" --sysroots "$RECEIPT" --target wasm32 -O3 -g "$sdk/examples/fortran/body.f90" -o robot.wasm
```

### Install C, C++ or Fortran with a site-provisioned toolchain

When your operator has provisioned the LLVM toolchain, sysroot and signed release for your selected SDK revision, use the site profile they supply. For example, in Bash with a trusted full commit ID in `REV`, run this single installation command:

```sh
set -o pipefail
curl --fail --silent --show-error "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$REV/install/bootstrap.py" | python3 -I -B - install --commit "$REV" --platform unitree --language c --site-profile /etc/wros/c-site.json
```

Build a C program using the installed compiler. The qualified row sets the default address width, threading, exception mode, optimization and debug symbols.

```sh
"$HOME/.local/share/wros-sdk/$REV/unitree/c/development/bin/wrc" main.c -o app.wasm
```

For Fortran, the site toolchain also provides the reviewed WebAssembly Flang and its matching MTE helper. The signed statement must cover Fortran and the C and C++ drivers that build its bridge and runtime, all for the same profile, build settings and VM. Select only the Fortran development package for Unitree.

```sh
curl --fail --silent --show-error "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$REV/install/bootstrap.py" | python3 -I -B - install --commit "$REV" --platform unitree --language fortran --site-profile /etc/wros/fortran-site.json
```

Build the installed example with the signed site defaults.

```sh
sdk="$HOME/.local/share/wros-sdk/$REV/unitree/fortran/development"
"$sdk/bin/wrf" "$sdk/examples/fortran/body.f90" -o robot.wasm
```

The operator supplies a local JSON file with these fields. Replace the example paths and digest placeholders with the reviewed values.

```json
{
  "toolchain": "/opt/wros/llvm",
  "sysroots": ["/opt/wros/wasm32-eh/sysroots.json"],
  "trust": {
    "verifier": "/opt/wros/bin/cosign",
    "verifier_sha256": "<approved verifier SHA-256>",
    "policy": "/etc/wros/release.policy",
    "statement": "/etc/wros/release.wasm",
    "statement_sha256": "<approved signed statement SHA-256>"
  }
}
```

The statement must contain one qualifying row for the selected language. If it contains several, add `release_sha256` with the canonical row digest from the qualification tool. Installation checks the signature, compiler, sysroot files and selected SDK, and prints `site_release_sha256`. Each strict build checks its own inputs and signed qualification again. The host tools and signed statement remain at their operator-managed paths. Reinstalling the same profile rechecks it. Select a fresh prefix when changing profiles. For C++, select `--language cpp` and use `bin/wrcc` with a C++ release.

### Revision hook and package format

At the selected commit the fixed entry is `install/revision.py`. The bootstrap invokes it with Python's isolated mode, positional platform and language identifiers, and the arguments following `--`. For `revision-help` it appends `--revision-help` and reads a JSON object containing a `help` string. A successful selection prints one JSON object, for example:

```json
{"variant":"bindings","packages":["platforms/unitree","metadata/cpp","license","bindings/c"]}
```

Each package name resolves to `install/packages/<name>.json` at that same commit. The `files` array lists repository-relative paths with their `bytes`, lowercase SHA-256 and decimal POSIX `mode` (420 or 493). A path present in two packages must have identical metadata. The bootstrap accepts up to 64 packages, 8,192 unique files, 128 MiB per file and 1 GiB of payload per selection. It places the installation under `<prefix>/<commit>/<platform>/<language>/<variant>` and returns this path as `directory`. Revision authors must keep the base CLI and this hook contract usable by the initial bootstrap. The installer matrix in `tests/install_protocol_matrix.py` checks the actual payload set for every registered language and platform using Git objects from a specified commit.

## C and C++ applications

`wrc` compiles C and `wrcc` compiles C++. Supply a Wasm-only MTE-capable toolchain prefix and the matching build receipt. The build recipes are in `tools/wasm/memtag`. Each closure binds its compiler digest, headers, libraries, target width, core features, MTE mode, thread mode and C++ exception ABI.

```sh
bin/wrc --toolchain "$PRODUCER" --sysroots "$RECEIPT" --reactor --export _start -O3 -g -o robot.wasm robot.c
```

Defaults are wasm32, Core 3.0, WasmMTE, standard Wasm exceptions and single-threaded output. Select `--no-mte`, `--target wasm64`, `--no-eh`, `--core mvp` or `-pthread` explicitly. A pthread-dependent build must propagate the thread option. Missing matching sysroot inputs stop the build. C++ EH and no-EH use distinct library closures. After link, the driver checks binary import signatures before replacing the output. It admits the ROSv2 contract, WASIp1 environment queries, clock reads, clock resolution queries and process exit, and the selected thread import. The VM independently enforces deployed permissions.

### Separate compilation and static libraries

Compile one translation unit with `-c`, create an indexed archive with `wrar`, then link the objects and archives. All invocations must select the same guest profile and compiler. C and C++ objects can share that profile. `-I` / `--include-dir`, `-D` / `--define` and `--std` support project headers, object-like definitions and the language standard. Link flags are limited to the documented Wasm frontend options; arbitrary native compiler or linker options are not forwarded.

```sh
bin/wrcc --toolchain "$PRODUCER" --sysroots "$RECEIPT" -O3 -g \
  --std c++20 -I include -DROBOT_AXES=6 -c control.cpp -o control.o
bin/wrar --toolchain "$PRODUCER" -o libcontrol.a control.o
bin/wrcc --toolchain "$PRODUCER" --sysroots "$RECEIPT" -O3 -g \
  --reactor --export _start main.cpp libcontrol.a -o robot.wasm
```

`wrar` creates a deterministic ordinary GNU archive using the selected prefix's `llvm-ar`; it never executes a guest or installs a native library. Objects contain a `wros.sdk.object` custom section binding their bytes to the exact compiler digest, pointer width, Core version, MTE, thread and EH settings. A mismatch, changed object, unmarked object, native ELF file, LLVM bitcode input or thin archive fails before linking. These build notes are not signatures: a user able to replace build inputs can also manufacture a note. Select a trusted compiler prefix and signed deployment artifacts. The VM remains the security boundary.

The linker frontend validates every archive member, including unused members, snapshots the object bytes in a private directory, and regenerates the symbol index before invoking the linker. It admits at most 1,024 objects, 128 MiB per object/archive and 256 MiB total object/archive input. Final output has a 128 MiB limit. Failed validation or compilation preserves the previous output. Build notes are removed from the final Wasm and its actual imports are checked independently; an allowed object profile never authorizes filesystem or socket imports.

The SDK accepts `clock_time_get` and `clock_res_get`. For wasm64, append `_wasm64` to each import name. Both widths use i32 clock IDs and i64 precision. Only the output pointer width changes. At deployment, realtime and monotonic clocks each have independent time and resolution grants.

For wasm64, the narrow environment allowance uses UWVM's explicit `environ_get_wasm64` and `environ_sizes_get_wasm64` signatures with i64 pointers, plus `proc_exit_wasm64`. These are the matching sysroot's extension to Preview1, not a standardized Preview1 memory64 ABI. wasm32 spellings are not interchangeable. Missing memory64 thread startup support refuses explicitly.

The SDK sysroot recipe selects libc++abi's upstream bare-metal configuration and silent terminate handler, together with digest-locked runtime diagnostic patches. The patches keep assertion checks and fatal Wasm traps while removing internal stderr output and unwinder environment-controlled tracing, including assertion-enabled builds. Exception propagation remains intact. They do not suppress application logging or grant permission to an external operation. Application diagnostics should use an authorized ROSv2 operation. The sysroot is compiled with optimization and full debug information; every selected header and library is hash-checked before frontend compilation.

`tests/separate_compilation.py` exercises real wasm32/wasm64 objects, archives, cross-file exceptions, denied mixtures and environment permission behavior in both VM engines. Run it under the VM repository's cgroup gate. A successful scoped receipt is not certification of every standard library operation, a whole ROS package, or a manufacturer's hardware.

Include `<wros/scene.h>` for the raw ABI. Rust and AssemblyScript declarations live under `language/`. These declarations cover the 163 registered operations in the captured VM catalogue. Their existence alone does not qualify a language frontend, a migrated ROS package or a device.

## Platforms and migration

The platform directory is open to additional Chinese and international manufacturers. Each platform records pinned source references. Implement pure transformations in Wasm and route native device access through authenticated external drivers. A new VM extension requires a concrete host-enforced permission that the common contract cannot express. The upstream fetcher obtains licensed vendor artifacts from the approved supplier. The deployer consumes their local paths and verified digests. Source references, simulator qualification and hardware qualification are independent records.

The registry contains 29 legacy identifiers and 32 platform scopes. It includes WAT and a C FFI bridge. The standard development installer provides C, C++, constrained D, numerical Fortran, JavaScript, Lua, Nim, Objective-C, Rust no_std, TinyGo and a freestanding scalar C# profile. Java and Kotlin use the synchronous AOT compiler in the default development selection. The compiler, standard library, memory-tagging coverage and accepted target options vary by profile. A registered platform can run a portable algorithm independently of whether its vendor driver or middleware has been exercised.

The C# compiler accepts the documented scalar profile and a typed scene ABI query. Managed CLR applications still need an integrated collector and runtime. For C++ migration, the Jazzy tf2 port adds a strict single-executor BufferCore overlay. The threaded build needs a separately qualified sysroot. The linked guides identify prerequisites, commands and tested application boundaries. [C#](csharp.md) · [Java and Kotlin](jvm.md) · [Jazzy tf2](tf2-buffer-port.md)

Industrial builds bind each object to the compiler digest, the selected guest profile (including MTE on or off) and a digest of the selected sysroot inventory. Recompile older objects before linking. The build verifies compiler-rt and the selected header and library files. Treat the producer, sysroot receipt and build inputs as trusted. The optimizer can omit a stack tag only when its analysis proves the relevant accesses stay within bounds and lifetime. A passing regression suite is evidence for the tested paths; it cannot establish whole-program memory safety.

Every published language compiler must support WasmMTE. Tagging is enabled by default. Select `--no-mte` for the whole target and provide the corresponding sysroot. C/C++ declarations can change instrumentation locally through Clang source attributes such as `no_sanitize("memtag")`. This is an author decision. Automatic tag elision requires compiler analysis of the object and all its uses.

[TinyGo](tinygo.md) · [Fortran](fortran.md) · [Rust](rust.md) · [Objective-C](objectc.md)

### Supported Wasm format

The SDK builds and runs WebAssembly **core modules** at the selected core feature level. It rejects WASI Preview 2 and Preview 3 targets, Component Model binaries, component-type metadata, and component ABI imports and exports. The same rule applies to separately compiled objects and every member of a guest static archive. SDK programs use the ROSv2 core imports. A selected Preview 1 clock or environment import still requires its own VM permission. A Core 3.0 feature selection does not select a WASI version.

## Run the external driver simulation

From a source checkout, `tests/mujoco_guest.py` compiles a controller in the selected language, runs it on the real VM and connects it to an external MuJoCo humanoid receiver over authenticated TLS. Provide the VM test sources, its executable, the matching OpenSSL build and the official MuJoCo distribution including the model. Use a fresh output directory on each run.

```sh
python3 tests/mujoco_guest.py --language lua \
  --vm-source "$VM_SOURCE" --runtime "$VM" --openssl-root "$OPENSSL" \
  --mujoco "$MUJOCO" --toolchain "$TOOLCHAIN" \
  --sysroots32 "$SYSROOTS32" --sysroots64 "$SYSROOTS64" --output "$OUT"
```

The test covers C, C++, Fortran, Lua, Nim and Objective-C on wasm32 and wasm64. Rust no_std and TinyGo use their supported wasm32 profiles. Pass `--rustroot` for Rust, `--goroot` and `--tinygoroot` for TinyGo, and `--producer` for Nim. The Objective-C route also requires `--objc-clang`, `--objc-runtime32` and `--objc-runtime64`. Fortran accepts `--flang`. The suite checks native agreement after 128 physics steps, rejection of an out-of-range command, and the reported state after a receiver crash in both VM engines. Inspect `results.json` for the executable and input digests, applied policy, backend, effects and native reference. A test of a development producer can explicitly pass `--candidate-mte`. It runs with instrumentation and does not produce a signed toolchain qualification.

For the Unitree Go2 model, set `SDK` to a signed Unitree D development installation and `GO2_ASSETS` to the vendor model directory named by the VM profile. The fixture builds a wasm32 BetterC controller for each case and verifies its receipt with the installed `wrd`. Both VM engines exercise the typed driver calls for normal stepping, a rejected command and a receiver crash.

```sh
python3 tests/mujoco_guest.py --language d --installed-sdk "$SDK" --address-bits 32 \
  --vm-source "$VM_SOURCE" --runtime "$VM" --openssl-root "$OPENSSL" --mujoco "$MUJOCO" \
  --vendor-model "$VM_SOURCE/test/0084.ros-runtime/mujoco_profiles/unitree-go2.json" \
  --vendor-assets "$GO2_ASSETS" --output "$OUT"
```

For a signed TinyGo site, use the Unitree TinyGo development directory as `SDK` and replace `--language d` with `--language tinygo`. The fixture builds the Go controller with the installed `wrtg` and verifies its build receipt against the VM before running each scenario.

The Java and Kotlin synchronous AOT package uses `set_wros_jvm_main(class_name)`. See [JVM compiler and Xmake options](jvm.md).

[JavaScript interpreter and ROS operations](js.md)
