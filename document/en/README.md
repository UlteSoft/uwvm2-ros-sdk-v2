# WROS SDK developer guide

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

The stable operations are `plan`, `install` and `revision-help`. Pass revision-specific options after `--`. Select `--component protocol` for the language-neutral contract and platform source references, or `--component compiler-source` for the C/C++ compiler and sysroot build inputs. The latter includes pinned source archives and patches. The ordinary development selection excludes those archives. The minimum Python version also applies to the preinstalled bootstrap.

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

Defaults are wasm32, Core 3.0, WasmMTE, standard Wasm exceptions and single-threaded output. Select `--target wasm64`, `--no-mte`, `--no-eh`, `--core mvp` or `-pthread` explicitly. A pthread-dependent build must propagate the thread option. Missing matching sysroot inputs stop the build. C++ EH and no-EH use distinct library closures. After link, the driver checks binary import signatures before replacing the output. It admits the ROSv2 contract, limited WASIp1 environment/exit operations, and the selected thread import. The VM independently enforces deployed permissions.

Include `<wros/scene.h>` for the raw ABI. Rust and AssemblyScript declarations live under `language/`. These declarations cover the 163 registered operations in the captured VM catalogue. Their existence alone does not qualify a language frontend, a migrated ROS package or a device.

## Platforms and migration

The platform directory is open to additional Chinese and international manufacturers. Each platform records pinned source references. Implement pure transformations in Wasm and route native device access through authenticated external drivers. A new VM extension requires a concrete host-enforced permission that the common contract cannot express. The upstream fetcher obtains licensed vendor artifacts from the approved supplier. The deployer consumes their local paths and verified digests. Source references, simulator qualification and hardware qualification are independent records.

The legacy registry supplies 29 language identifiers and 32 platform identifiers. C and C++ have compiler drivers here. The remaining compiler/runtime closures, high-level language bindings, vendor products and source-compatibility layers for rcl, rclcpp, rclpy and rcljava require separate implementation and execution evidence.
