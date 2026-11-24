# C-family execution matrix

The runner builds one pinned library workload with each installed C, C++, Objective-C or Objective-C++ frontend. Its plan has 640 cells across five Linux host ABIs. Each host and language has sixteen combinations of guest pointer width, exception handling, threads and SIMD for each MTE setting. `--list` prints one JSON object per planned cell. Execution collects the cells for one host per invocation. [Acceptance criteria](../../../../document/en/qualification.md#c-family-execution-comparisons)

## Run one cell

Use a checkout containing both `src/qualification/cfamily` and `src/qualification/objc`. Run Python 3.11 or later outside the installed generic binary SDK. Set `C_SDK` to its installed C selection, `VM` to the WROS executable, `DECODER` to the qualification instruction decoder and `WASMTIME` to the 42.0.1 release CLI. The C API adapter build is described below. Run release measurements inside the qualification environment and keep its isolation receipt with the results.

```sh
suite="$PWD/src/qualification/cfamily/execution_performance"
scratch="$PWD/.tmp/execution"
mkdir -p "$scratch/tmp"
export TMPDIR="$scratch/tmp"
python3 -I -B "$suite/matrix.py" --list > "$scratch/plan.jsonl"
python3 -I -B "$suite/matrix.py" \
    --host linux-x86_64 --language c --cc-sdk "$C_SDK" \
    --profile wasm32-wasip1-noeh-nomte --simd on \
    --vm "$VM" --decoder "$DECODER" \
    --wasmtime-host "$CAPI_HOST" --wasmtime-cli "$WASMTIME" \
    --work "$scratch/lz4-wasm32"
```

The VM must match a build or installed host-tools receipt. `--vm-receipt FILE` selects its location. `--vm-target FILE` selects the intended revision using the fields `vm_commit` and `vm_tree`. The default target is the SDK's reviewed runtime qualification pin. Build the decoder from its locked Cargo manifest with the qualified vendored dependencies. [Decoder source](../decoder) · [VM identity and shared-memory policy](../sysroot_suite.py)

A complete host run uses all four installations. Set `CXX_SDK`, `OBJC_SDK` and `OBJCPP_SDK` to their respective installed roots. Set `WAVM` to the adapted mt-2 binary. The same command runs inside an AArch64 system-QEMU guest using `--environment system-qemu` and that guest's VM and reference ELFs.

```sh
python3 -I -B "$suite/matrix.py" \
    --cc-sdk "$C_SDK" --cxx-sdk "$CXX_SDK" \
    --objc-sdk "$OBJC_SDK" --objcpp-sdk "$OBJCPP_SDK" \
    --vm "$VM" --decoder "$DECODER" --wasmtime-host "$CAPI_HOST" \
    --wasmtime-cli "$WASMTIME" --wavm "$WAVM" \
    --work "$scratch/full-host"
```

The runner infers the host from the VM's ELF header. Valid selectors include `--width 32|64` and `--eh`, `--threads`, `--simd`, `--mte` with `on|off`. `--language objc --mte on` selects sixteen cells. Each independent run takes an empty work directory. The default is a fresh directory under the checkout's `.tmp`. Compiler temporaries, caches, captures and generated Wasm stay within the run. `--cpu N` chooses the logical CPU. `--samples N` sets an even number of pairs, with ten by default. `--correctness-only` or `--environment user-qemu` collects functional evidence only. `--isolation-receipt FILE` records the external isolation receipt's hash.

## Workloads and expected output

- C compresses and decompresses sixteen deterministic 16 KiB blocks with LZ4 v1.10.0, checks the round trip, then hashes the decoded bytes. The timed loop processes 8 MiB of input. [LZ4 source pin](../external-libraries.json) · [Guest](lz4.c)
- C++ uses the existing fast_float v8.0.2 parser fixture on 262,144 strings. Its fixed batch fits the 128-page shared memory in both guest ABIs. The host computes the expected bits from the same decimal inputs with Python's binary64 conversion. [Source pin](../external-libraries.json) · [Guest](workloads.cpp)
- Objective-C runs the existing GCC Object client, then times 65,536 dispatches through GCC 15.2.0's `class` and `isEqual:` methods on two live objects. [Source pin](../../objc/upstreams.json) · [Client](../../objc/clients/gcc-object.m) · [Guest](gcc-object.m)
- Objective-C++ runs the Chromium 143 swizzler client, then times 4,096 scoped swaps, calls to the original implementation and restored dispatches. The independent oracle sums the two original scores and the replacement score. [Source pin](../../objc/upstreams.json) · [Client](../../objc/clients/chromium-swizzler.mm) · [Guest](chromium-swizzler.mm)

Each cell records the installed selection, frontend, sysroot closure, upstream commits, source hashes, exact build arguments, SDK sidecar, actual imports and linked-opcode counts. A threaded profile uses an owner with the same limits as the guest's shared `env.memory`. The workload runs on one guest thread. An EH or SIMD setting records which operations the compiler may use. The opcode counts show what appeared in the linked module. Dedicated feature probes exercise exception paths and alternative vector and bulk-memory lowering. [ISA qualification](../../../../document/en/cfamily-optional-instructions.md)

## Reference engines

Build the timed C API adapter from the official Wasmtime 42.0.1 C API archive for the machine that will execute it. `CAPI` points to the extracted archive. The adapter reuses the existing permissions, shared-memory implementation and host clock. It selects native Cranelift explicitly and reports the target on stderr. The runner also recognizes the exact static x86_64 host in the prior C++ receipt. A conventional unverified C API build can supply correctness observations. [C API pin and archive verification](../wasmtime_reference/README.md) · [Published x86_64 host identity](../../../../document/qualification/cfamily-cpp-wasmtime-execution.json)

```sh
c++ -std=c++17 -O2 -I"$CAPI/include" "$suite/native-wasmtime-host.cpp" \
    "$CAPI/lib/libwasmtime.a" -ldl -lpthread -lm -o "$scratch/qualification-host"
export CAPI_HOST="$scratch/qualification-host"
```

The stock CLI supplies an independent comparison for private wasm32 guests. The C API adapter also implements the SDK's `_wasm64` interfaces and supplies the shared-memory owner when the guest's imports are supported. A stock wasm64 import or an unsupplied shared owner has a specific capability entry. An actual `wasi.thread-spawn` import exceeds the C API adapter's current coverage. Wasmtime 32-bit Pulley observations are diagnostic. The runner checks the reference ELF, the VM ELF, the selected execution environment and the native compilation backend before computing a performance ratio.

For a tagged module, supply WAVM mt-2 with the WROS wire and private ownership patches. The runner verifies the exposed ownership and checked software-MTE options, fingerprints the executable and loaded WAVM library, and enables direct tail calls if the build advertises them. Shared ownership and 32-bit WAVM hosts remain open under this port. Unsupported opcodes and unresolved imports retain their diagnostics. The WROS software-MTE comparison executes the same tagged guest with checking enabled and disabled, including when the external reference is unavailable. [WAVM source and build](../wavm_reference/UPSTREAM.md)

## Read the evidence

Every engine executes a guest warmup before the monotonic timing interval. The runner first checks WROS INT, balanced LLVM AOT and each applicable reference against the expected item count, checksum and runtime tag witness. The C API also verifies the reported interval against its independent host clock log. Each timed pair alternates the launch order on the same logical CPU. Guest initialization, compilation, instantiation, warmup, output validation and process startup fall outside the reported guest interval.

`inputs.json` identifies the inputs and engines. Each cell has its Wasm, compiler output, decoder output, raw stdout and stderr, plus its own `result.json`. `results.jsonl` records all observations. `summary.json` counts completed cells and per-reference outcomes. Ratios divide WROS AOT nanoseconds by the matched reference nanoseconds. The report gives every paired sample, the median of paired ratios, quartiles and range. Exit 0 means all selected cells obtained an external timing and met the applicable MTE threshold. Exit 77 records open comparisons. Exit 1 records failures or a software-MTE median above 1.5.
