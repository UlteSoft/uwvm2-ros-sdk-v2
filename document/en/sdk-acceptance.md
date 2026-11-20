# SDK language and platform acceptance

[中文](../zh/sdk-acceptance.md)

Run the matrix from a source checkout with the selected commit available locally. Use the designated 64 GiB zero-swap test cgroup. Compilers and VM tests run serially. The receipt records the exact SDK commit, cgroup, fixture digests, Xmake and VM identity.

~~~sh
$GATE python3 -B tests/sdk_acceptance.py \
  --commit "$SDK_COMMIT" --language wat --language as \
  --platform unitree --platform universal_robots \
  --platform-case migration --vm "$VM" --xmake "$XMAKE" \
  --output .tmp/sdk-acceptance
~~~

Repeat the language and platform options to select a subset. Omitting either option selects every registered value for that dimension. The first selected platform is the common example location unless you set --contract-platform. The second tier executes the extension and migration projects for each selected pair by default. Repeat --platform-case to choose the desired categories. Use --plan to list the requested cases and known prerequisites without starting build or execution jobs.

Installed platform projects run after the corresponding language check passes. A supplied artifact can be tested independently. For an SDK revision containing the WAT profile fixtures, the WAT language check additionally runs the Core 3.0, shared-memory, WasmMTE and real-child cases once. Language checks without a joint-profile fixture record `joint_profile.outcome` as `not_exercised`. The aggregate `all_joint_profiles_passed` requires explicit joint evidence for every selected language.

The optional --inputs file uses the wros-sdk-acceptance-inputs-v1 schema. Site and artifact paths are relative to that file, or absolute. A platform-specific profile overrides the language default. For signed sites, provide the configuration that the SDK installer already verifies. For C#, F# and Visual Basic, provide managed_host from the matching host preparation command and managed_toolchain for the matching Wasm LLVM. Bundled AssemblyScript, standard Go and WAT can run without a site.

A producer that uses explicit local tools may select toolchain and sysroots instead of a site. Give the Wasm LLVM prefix and the matching sysroot manifest. The selected compiler still checks its own profile and admission rules.

~~~json
{
  "schema": "wros-sdk-acceptance-inputs-v1",
  "profiles": {
    "c": {"site": "wasm32-c-site.json"},
    "unitree/c": {"target": "wasm64", "site": "wasm64-c-site.json"}
  },
  "artifacts": {}
}
~~~

To exercise a supplied core Wasm module, add an entry under artifacts keyed by platform/language/case, such as unitree/wat/migration. Supply file and the exact lowercase SHA-256 as sha256. Optional profile fields are address_bits, wasm_version, threads, mte and exceptions. The defaults select wasm32, Core 3.0, a single thread, MTE and no EH. The optional queries array declares read-only test grants and is empty by default. The runner validates the digest and SDK import policy, then boots the exact bytes in both VM engines. This case provides execution evidence for those bytes. Compiler and vendor-driver qualification still require the corresponding source fixtures.

The versioned results.json distinguishes three outcomes.

- executable records both engine results and the Wasm digests.
- blocked records an unavailable prerequisite, failed fixture or rejected artifact.
- not_exercised records an absent example or a plan-only case.

A normal run returns zero only when every requested row is executable. Logs and child fixture receipts remain in the output directory. Temporary installations and objects are removed after each case. The platform extension fixture covers the SDK's authenticated local permission boundary. Official simulation and physical vendor drivers use dedicated acceptance fixtures.

## Upstream C library tests

The upstream replay builds library sources from pinned GitHub commits and uses
the upstream test implementations. It records the native control, strict
`wrc` build receipt, guest imports, decoded WasmMTE operations and both VM
engine results. Use a separate source directory inside the local test
workspace, and run the suite through the shared 64 GiB test gate.

```sh
mkdir -p "$SOURCES"
git clone --depth 1 --branch 6.7.3 https://github.com/ros2/rcutils.git "$SOURCES/rcutils"
git clone --depth 1 --branch v1.7.19 https://github.com/DaveGamble/cJSON.git "$SOURCES/cjson"
git clone --depth 1 --branch v1.3.2 https://github.com/madler/zlib.git "$SOURCES/zlib"
"$GATE" /usr/bin/python3 -B tests/upstream_c_libraries.py \
  --sdk "$PWD" --sources "$SOURCES" --commit "$SDK_COMMIT" \
  --site "$SIGNED_C_SITE" --vm "$WROS_VM" --output "$OUTPUT"
```

The selected C site must authorize the wasm32 Core 3.0 EH profile at
`-O3 -g` with MTE. A case can be repeated with `--case`. The wrapper
uses the upstream rcutils byte-array assertions with stderr diagnostics
disabled, the cJSON in-memory Unity tests with a guest output sink, and
the upstream zlib example with the project's `Z_SOLO` option. The guest
import policy grants only the declared read-only clocks. The cJSON corpus
replay embeds the exact upstream JSON inputs and expected outputs in the
guest. Gzip file access and the rest of the ROS middleware have separate
porting requirements.

The static archive replay takes the preceding output, compiles the eight
zlib source files separately, runs the SDK's `wrar`, and relinks the same
upstream test.

```sh
"$GATE" /usr/bin/python3 -B tests/upstream_zlib_archive.py "$PWD" "$OUTPUT" \
  "$SOURCES/zlib" "$SIGNED_C_SITE" "$WROS_VM" "$ARCHIVE_OUTPUT"
```

## Upstream Go and Python libraries

Use the signed wasm32 TinyGo EH and MTE site to replay the `xxHash` v2.3.0
library. The guest adapter preserves the upstream functional test bodies and
assertions, including all 148 `TestAll` subtests. The upstream host allocation
measurement remains in the native control.

```sh
git clone --depth 1 --branch v2.3.0 https://github.com/cespare/xxhash.git "$SOURCES/xxhash"
"$GATE" /usr/bin/python3 -B tests/upstream_go_libraries.py --sdk "$PWD" \
  --source "$SOURCES/xxhash" --commit "$SDK_COMMIT" --site "$SIGNED_TINYGO_SITE" \
  --vm "$WROS_VM" --output "$GO_OUTPUT"
```

The CPython replay uses the original ROS `angles` unittest methods and PyPA
`packaging` version cases. [Python replay instructions](../../tests/cpython/upstream-libraries.md).

## Upstream Rust and interpreter libraries

Use a signed wasm32 Rust site with the Core 3.0, no-EH, single-thread profile
at `-O3 -g` to replay ArrayVec 0.7.7. The native control runs the upstream
integration suite with default crate features disabled. The guest runs 26
original test bodies for inline vectors, UTF-8 strings, capacity handling,
iteration, draining and value drops. Its test entry uses `core` and redirects
test panics to a Wasm trap. Tests that require host services, heap-backed
standard-library objects or unwinding run only in the native control.

```sh
git clone --depth 1 --branch 0.7.7 https://github.com/bluss/arrayvec.git "$SOURCES/arrayvec"
"$GATE" /usr/bin/python3 -B tests/upstream_rust_libraries.py --sdk "$PWD" \
  --source "$SOURCES/arrayvec" --commit "$SDK_COMMIT" --site "$SIGNED_RUST_SITE" \
  --rustroot "$RUST_ROOT" --vm "$WROS_VM" --output "$RUST_OUTPUT"
```

To compare an explicit MTE opt-out, replace `--site` with
`--toolchain "$WROS_LLVM" --plain-sysroots "$PLAIN_NOEH_SYSROOT"` and choose a
fresh output directory. The strict path records the decoded managed stack
instructions, the signed VM identity and the results from both engines.

The QuickJS and mruby replays have their own input pins and adaptation
boundaries. [Interpreter library replay instructions](../../tests/script-libraries/README.md).
