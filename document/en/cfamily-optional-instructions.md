# Optional Wasm instruction generation in the C-family SDK

The installed `wrc`, `wrcc`, `wroc`, and `wrocxx` commands accept two independent switches. Core 3.0 enables both by default. The last switch for each family wins.

- `-msimd128` enables SIMD128. `-mno-simd128` disables both SIMD128 and relaxed SIMD for the translation unit. Ordinary vectorizable arithmetic can then lower to scalar Wasm.
- `-mbulk-memory-opt` allows LLVM to select `memory.copy` and `memory.fill`. `-mno-bulk-memory-opt` selects scalar fallbacks for ordinary `memcpy`, `memmove`, and `memset` calls. A disabled build links weak guest implementations that use byte loads and stores. Application-provided strong definitions take precedence.
- On an unthreaded target, disabling the copy optimization also disables the native LLVM bulk-memory target feature because it implies the optimization. The WASIp1 thread ABI requires the full feature for TLS and atomic shared-memory initialization. On that target the driver keeps the full feature and disables Clang's builtin recognition for the three ordinary C memory calls. Explicit compiler intrinsics, compiler-generated aggregate operations, prebuilt libraries and LLD-generated startup functions can still contribute optional instructions. The driver keeps the selected pointer width, MTE and EH configuration.
- A build receipt requested with `--build-receipt` records the application settings in `optional_isa`, including the actual Clang overrides. A separately compiled object records explicitly disabled families. An older object can participate in a default link. A link that requests a disabled family requires its application objects to have been compiled with that restriction. The existing strict memory-release attestations cover their original code generation settings.

For example, compile an ordinary Wasm64 C++ application with scalar vector code and native bulk copy enabled.

```sh
/sdk/cpp/bin/wrcc --target wasm64 --core 3.0 --no-threads --no-mte --no-eh \
  -O3 -mno-simd128 -mbulk-memory-opt --build-receipt example.cpp -o example.wasm
```

## Qualify the final module

The suite builds 256 modules across four languages, sixteen combinations of pointer width, MTE, threads and EH, and the four SIMD/copy settings. Both u2ros INT and LLVM AOT execute every linked and decoded module, including modules that fail the instruction check. The runtime binary and its build receipt must match the selected VM pin.

```sh
cargo build --release --locked --offline --manifest-path src/qualification/cfamily/decoder/Cargo.toml
python3 src/qualification/cfamily/optional_isa_suite.py \
  --cc-sdk /sdk/c --cxx-sdk /sdk/cpp --objc-sdk /sdk/objc --objcpp-sdk /sdk/objcpp \
  --vm /opt/tools/bin/uwvm2-ros \
  --decoder src/qualification/cfamily/decoder/target/release/decode-memtag \
  --work /work/isa-matrix --seed 0x12345678 --jobs 4
```

Run a single cell by adding `--language objc --profile wasm32-wasip1-threads-noeh-mte --simd off --bulk on`. Only the selected language's SDK path is required. Use an empty output directory for each run. A VM built from a different revision can be selected with `--vm-target` pointing to a JSON file containing the reviewed `vm_commit` and `vm_tree`, and `--vm-receipt` pointing to that binary's build receipt.

Each program allocates real heap storage, calculates 64 unsigned vector lanes, fills a subrange, and performs overlapping moves in both directions followed by a zero-length move. Objective-C uses a class message and Objective-C++ also instantiates a C++ template. The operation sources and seed sequence are identical across the four code generation settings. The fixed seeds include zero, one, the high bit, and all bits set. `--random-cases` sets the additional case count, with four by default. Omitting `--seed` selects a random seed and records it in `inputs.json`.

The independent Python model writes `expected.bin` with the seed, every lane, the unsigned sum and every byte of the 64-byte buffer after each memory operation. Both engines must emit exactly those bytes. The row records the first differing offset when a comparison fails.

The decoder walks actual operators in function bodies and constant expressions. It requires packed arithmetic in the vector kernel when enabled, scalar accesses on the fallback path, and the selected copy/fill behavior in the two memory kernels. It separately counts ordinary SIMD, relaxed SIMD, `memory.copy`, `memory.fill`, other bulk operations, threads, and MTE. `memory.init`, `data.drop` and atomics can be required by thread startup. A disabled SIMD or copy/fill instruction anywhere in the final module fails the cell. For example, heap support can pull in precompiled libc operations, and LLD can emit `memory.fill` in shared-memory BSS initialization. `result.json` identifies the offending functions. The shared memory owner used by threaded runs contains a memory definition and an export, with no code section.

Each cell retains the executable, build receipt, decoder listing, exact command arguments, stdout and stderr from both engines, and its result. `summary.json` reports instruction and execution outcomes separately. A zero process exit requires all selected cells and both engines to pass.

## Reproduce the public x86_64 run

Run the following in an empty project directory inside the qualification namespace. The installer reports the installed directory for each selection. The public run used the 64 GiB parent and child cgroups, zero swap, an empty home, and a project-disk scratch directory. After installation the tests ran in a network namespace with only the loopback interface.

```sh
SDK_COMMIT=38023bff47eb545815bdc7e272fc24c44901686d
mkdir -p .tmp/sdk-install
export TMPDIR="$PWD/.tmp/sdk-install"
curl -fL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$SDK_COMMIT/install.py" -o install.py
for language in c cpp objc objcpp
do
  python3 -I -B install.py install --commit "$SDK_COMMIT" --language "$language" --platform generic --mode binary --prefix "$PWD/sdk" > "$language.install.json" || exit 1
done
```

The qualification target is a Core Wasm module using WASIp1. A feature required by a language runtime is a prerequisite. For example, keep WasmGC enabled when a Java or C# backend requires it. Component Model, WASIp2, WASIp3 and ROS integration are outside this suite.
