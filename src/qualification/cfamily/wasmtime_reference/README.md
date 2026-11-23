# Wasmtime reference for the external C/C++ qualification suite

This opt-in host runs each original non-MTE Core module from the external suite on Wasmtime's Cranelift engine. Use the stock Wasmtime CLI results to assess stock WASIp1 compatibility. Use the adapter results to compare guest execution with the recorded UWVM interpreter and AOT runs under the suite's capability profile.

## Reproduce on x86_64 Linux

Use the official Wasmtime 42.0.1 C API release, commit `6844a83b530f86ad13a65175282fe2dbcd33cad1`. Stage `wasmtime-v42.0.1-x86_64-linux-c-api.tar.xz` as a read-only input. Its published SHA-256 is `2097a47351918a446b26c7e65f487278f63bc947591b71897db547cd90c05082`. [Release](https://github.com/bytecodealliance/wasmtime/releases/tag/v42.0.1) · [C API archive](https://github.com/bytecodealliance/wasmtime/releases/download/v42.0.1/wasmtime-v42.0.1-x86_64-linux-c-api.tar.xz)

Run these commands in the qualification environment with a C++17 compiler and Python 3.11 or newer. In this example `/inputs/suite` is a read-only copy of `src/qualification/cfamily`, `/inputs/original` contains the original external suite's `inputs.json`, `results.jsonl` and per-case artifact and capture directories, and `/work` is the writable work directory. Give each rerun its own empty `--work` output directory.

```sh
set -eu
archive=/inputs/wasmtime-v42.0.1-x86_64-linux-c-api.tar.xz
reference=/inputs/suite/wasmtime_reference
mkdir -p /work/compiler-temporaries
export TMPDIR=/work/compiler-temporaries
printf '%s  %s\n' 2097a47351918a446b26c7e65f487278f63bc947591b71897db547cd90c05082 "$archive" | sha256sum -c -
tar -xJf "$archive" -C /work
capi=/work/wasmtime-v42.0.1-x86_64-linux-c-api
c++ -std=c++17 -O2 -I"$capi/include" "$reference/host.cpp" \
    "$capi/lib/libwasmtime.a" -ldl -lpthread -lm -o /work/qualification-host
/usr/bin/python3 -I -B "$reference/compare.py" --host /work/qualification-host \
    --results /inputs/original --work /work/wasmtime-adapter --jobs 2
```

The driver checks the manifest SHA-256, the complete 14-program by eight-profile matrix, each case source, each guest module, and each supplied shared-memory owner against the SDK evidence. It regenerates the original interpreter and AOT command lines from `sysroot_suite.py` and passes their verified per-import decisions and grants to the host. Wasmtime type-checks and instantiates the supplied Core bytes. Every run has a fresh store, host process, and pair of capture files.

## Host behavior

The private-memory profiles use the calling guest's public `memory` export. For shared memory, the host instantiates the recorded owner, obtains its `memory` export, and supplies that same Wasmtime shared memory handle as the guest's `env.memory` import. Every callback reads the current memory size after any guest growth. The 14 programs have no `wasi.thread-spawn` import. The adapter admits the observed Preview1 signatures, plus their SDK `_wasm64` forms with 64-bit pointers and sizes.

The host implements `clock_time_get`, `environ_get`, `environ_sizes_get`, `fd_fdstat_get`, `fd_write`, `proc_exit`, and `sched_yield` under the recorded grants. The monotonic clock returns host nanoseconds and records each value. The guest environment and preopen list are empty. The corpus imports no argument functions. Standard input is at EOF and `fd_read` is denied. Output descriptors identify the regular capture files and report write and file-metadata rights when granted. The adapter checks the full iovec array, each payload, and the return buffer before publishing guest bytes. It uses 8-byte entries on wasm32 and 16-byte entries on wasm64.

The suite denies `fd_close`, `fd_prestat_dir_name`, `fd_prestat_get`, `fd_read`, and `fd_seek`. These imports return Preview1 `ENOTCAPABLE` before accessing guest memory or a descriptor. Unknown imports, mismatched signatures, mismatched interface entries, and attempts to enable these five operations fail qualification setup.

## Reading the evidence

`stdout` and `stderr` contain the raw captured bytes. `host.log` records host calls, errno values, monotonic-clock observations, entry into `_start`, and either a normal return, the full `proc_exit` code, or an error. Each JSONL row compares the guest exit code and both streams to each saved engine run separately. The driver also checks the upstream answer file for cases that declare one. A saved engine's stderr can include engine diagnostics. The raw captures preserve those differences.

`inputs.json` identifies the host binary, source, driver, manifest, active suite policy, and original evidence by SHA-256. `summary.json` counts real guest terminations and the matches, differences, or unavailable comparisons for each engine. Exit status 1 preserves the completed evidence when any observable differs, an execution fails, or an upstream answer differs. Stock CLI reports and adapter reports use distinct output directories and reference labels.
