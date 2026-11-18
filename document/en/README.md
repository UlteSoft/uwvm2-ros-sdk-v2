# WROS SDK developer guide

[WasmMTE detection guarantees](memtag.md)

For driver/model security and the division between Wasm and deployment authority,
read [Local driver and model attachments](local-attachments.md).

[Build and run a Wasm project with xmake](xmake.md) · [Xmake API index](xmake-api-index.md)

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

The stable operations are `plan`, `install` and `revision-help`. Pass revision-specific options after `--`. Select `--component protocol` for the language-neutral contract and platform source references, or `--component compiler-source` to install the shared Wasm LLVM backend and sysroot build inputs alongside the selected language. C, C++, Fortran, Lua, Rust and TinyGo use this backend. The package includes the pinned backend source archives and patches. Language-specific compiler and runtime prerequisites are documented in each language guide. The ordinary development selection excludes those archives. The minimum Python version also applies to the preinstalled bootstrap.

For an existing compiler integration, pass `-- --component bindings` to install only the selected raw declarations, the licence, and the selected language and platform metadata. C and C++ share a header. This revision also publishes Rust and AssemblyScript declarations. This component fetches no compiler, compiler sources or full ABI catalogue. The original bootstrap can discover it with `revision-help` at this commit.

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

The legacy registry supplies 29 language identifiers and 32 platform identifiers. C and C++ have compiler drivers. Lua builds and embeds its interpreter. TinyGo builds a wasm32 program and its garbage collector. The numerical Fortran route compiles wasm32 and wasm64 programs. Rust builds a wasm32 no_std program with its core library. The remaining compiler/runtime closures, high-level language bindings, vendor products and source-compatibility layers for rcl, rclcpp, rclpy and rcljava require separate implementation and execution evidence.

Industrial builds bind each object to the compiler digest, the selected guest profile (including MTE on or off) and a digest of the selected sysroot inventory. Recompile older objects before linking. The build verifies compiler-rt and the selected header and library files. Treat the producer, sysroot receipt and build inputs as trusted. The optimizer can omit a stack tag only when its analysis proves the relevant accesses stay within bounds and lifetime. A passing regression suite is evidence for the tested paths; it cannot establish whole-program memory safety.

Every published language compiler must support WasmMTE. Tagging is enabled by default. Select `--no-mte` for the whole target and provide the corresponding sysroot. C/C++ declarations can change instrumentation locally through Clang source attributes such as `no_sanitize("memtag")`. This is an author decision. Automatic tag elision requires compiler analysis of the object and all its uses.

[TinyGo](tinygo.md) · [Fortran](fortran.md) · [Rust](rust.md)
