# WASIp1 sysroot qualification

The library suite compiles an upstream program through the installed `wrc` or `wrcc` and runs the resulting Core Wasm module in u2ros using INT and LLVM AOT. Both engines run the same file. The matrix crosses wasm32 and wasm64 with MTE, threads, and exception handling independently enabled and disabled.

The [manifest](../../src/qualification/cfamily/cases.json) identifies each source. The LLVM inputs come from LLVM 23.1.5. The Open POSIX tests come from the wasi-libc revision used by WASI SDK 34. The libc-test revision is the one requested by that wasi-libc release. Each pthread conformance test runs in the eight thread-enabled profiles. The remaining inputs run in all sixteen. [LLVM sources](https://github.com/llvm/llvm-project/tree/392dfff97d29b59d77e5cac6d4b6ef2585fe7117) · [wasi-libc sources](https://github.com/WebAssembly/wasi-libc/tree/2e6fb9d8ee0cdf9e431fbcabe8af3115de000a13) · [libc-test sources](https://github.com/bytecodealliance/libc-test/tree/18e28496adee3d84fefdda6efcb9c5b8996a2398)

Use the [runner](../../src/qualification/cfamily/sysroot_suite.py) inside the qualification namespace. Supply the installed C and C++ prefixes, the matching compiler sources, the installed WAT assembler, the VM, the opcode decoder, and an empty results directory on the project volume. The example uses the paths as mounted in that namespace.

The runner verifies the VM commit, source tree and executable SHA-256 before building cases. Pass `--vm-receipt /path/to/receipt.json` for a separate build. When mounting the suite separately, pass the reviewed `runtime-qualification.json` through `--vm-target`.

```sh
python3 -I -B /repo/src/qualification/cfamily/sysroot_suite.py \
  --cc-sdk /sdk/c --cxx-sdk /sdk/cpp --compiler-sources /repo/src/compilers/cc \
  --vm /opt/tools/bin/uwvm2-ros --wrwat /sdk/wat/bin/wrwat \
  --decoder /opt/tools/bin/decode-memtag --work /work/results --jobs 8
```

`inputs.json` records the tool, manifest, and runner hashes. Each line of `results.jsonl` identifies the source, profile, compiler arguments, guest digest, feature counts, WASIp1 imports, and each engine's outcome when a module was built. Each program's directory contains its compiler, decoder, INT, and AOT output. `summary.json` counts builds and executions separately. Upstream skips, unresolved POSIX outcomes, timeouts, and compiler failures have distinct labels. The runner returns a nonzero status when an applicable program did not pass both engines.

For third-party libraries, add `--suite external` and choose a second empty results directory. The fourteen programs use the same sixteen profiles. LZ4 exercises compression and decompression, cJSON runs three upstream Unity suites, uthash compares four upstream programs with their exact expected output, and fast_float runs four numeric parsing programs. The two SDK test clients exercise pugixml's XPath queries and tree mutation, and TinyXML-2's in-memory serialization and parsing. The manifest pins each project by commit and checks the Git blob of each vendored source, test and license. [Third-party inputs and programs](../../src/qualification/cfamily/external-libraries.json)

The compiler-specific subtraction fixtures live under the qualification tree. They cover the two integer widths, C and C++, ordinary typed pointer differences, the explicit subtraction builtins and the feature-off diagnostics. [Clang CodeGen and Sema regression sources](../../src/qualification/cfamily/clang)

## Wasmtime reference

Run the pinned Wasmtime 42.0.1 C API adapter on one producer host's sysroot evidence at a time. The reference machine needs its own executable adapter and opcode decoder. Mount the matching SDK sources and the producer's results read-only. Keep `inputs.json`, `results.jsonl`, `summary.json` and the eight non-MTE profile directories, including compiler receipts, captures and memory owners. [Adapter build instructions](../../src/qualification/cfamily/wasmtime_reference/README.md)

```sh
python3 -I -B /repo/src/qualification/cfamily/wasmtime_reference/compare.py \
  --suite sysroot --host /tools/qualification-host --decoder /tools/decode-memtag \
  --compiler-sources /repo/src/compilers/cc --results /original/sysroot \
  --work /work/sysroot-reference --jobs 2 --timeout 180
```

For a production replay, add `--qualification-receipt /original/evidence/sysroot-receipt.json` to verify the row and summary digests. Pass `--host-sha256` with the trusted adapter digest. The options `--vm`, `--vm-receipt` and `--vm-target` verify the producer VM against its binary, build receipt and reviewed commit/tree, including when its CPU differs from the reference machine.

The full manifest schedules 2,464 source/profile pairs, including 1,232 non-MTE pairs. Open POSIX runs only with threads enabled. The driver also accepts a producer selection recorded by `sysroot_suite.py --case` or `--profile` and reports its own denominator. It verifies original qualification counts, source and guest digests, compiler receipts, fresh opcode counts, actual imports, shared-memory bounds, and the exact INT and AOT commands. A compatible threaded guest receives its original `env.memory` owner.

Each `results.jsonl` row identifies the source, profile and original qualification. `match` requires a Wasmtime guest exit of zero, passing INT and AOT runs, and identical exit, stdout and stderr against each engine. The corresponding output directory contains raw captures and `host.log`. The summary counts real guest starts and terminations, case statuses by profile and family, and each unsupported import or grant.

An exact upstream skip, the missing `sem_unlink` link dependency and the pinned upstream `lsearch` test with undersized input records each have a separate status. The full-width SDK port has its own row. Cases requiring `wasi.thread-spawn`, argument-vector calls or a granted realtime `poll_oneoff` retain their import and permission details. These exclusions have unavailable engine comparisons. Exit 0 means every selected non-MTE cell matched. Exit 77 means all applicable guests matched and the remaining rows have documented limitations. Exit 1 records a difference, an unexpected failure or an evidence error.
