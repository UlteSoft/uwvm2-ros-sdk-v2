# C and C++ VM debugging, full restore and signed updates

One host run crosses 16 guest profiles with both languages, INT and LLVM AOT, and three capabilities. A full round contains 192 observations per host and 960 across Linux x86-64, i686, AArch64, ARM soft-float and ARM hard-float. The runner identifies the target host from the VM ELF header and records the controller architecture and optional emulator command separately. [Runner](../../src/qualification/cfamily/debug_suite.py) · [Fixtures](../../src/qualification/cfamily/debug_fixtures) · [中文](../zh/cfamily-debug-tests.md)

## Reproduce a host run

Use the offline qualification namespace with its 64 GiB limit, zero swap and project-volume scratch directory. Mount the installed C, C++ and WAT prefixes, the target VM and its receipt, the reviewed VM commit/tree JSON, and the qualification files read-only. The runner needs Linux Python 3.11 or later with Ed25519 support from `cryptography`. Copy `debug_suite.py`, `debug_live.py`, `sysroot_suite.py` and the adjacent `debug_fixtures/` together. The compiler prefixes can be outside the checkout. [Namespace launcher](../../src/qualification/isolated.py) · [Reviewed VM target](../qualification/runtime-qualification.json)

Supply a directory containing three public VM support files with their original relative paths. Their SHA-256 pins come from VM revision `454a19a3c8c1ea388472d44589a126554067ef8b`. The accepted runtime revision comes from the reviewed target and the measured VM executable receipt. [Debugger transport](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/test/0018.debugger/run_dump_launch_policy.py) · [Snapshot decoder](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/tools/debug/snapshot.py) · [Signed protocol helper](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/test/0017.runtime/run_signed_update_boundaries.py)

The example uses paths visible inside the namespace. Set `--round-id` to the same identifier on all five hosts and use a fresh output directory for each run.

```sh
python3 -I -B /work/qa/cfamily/debug_suite.py \
  --cc-sdk /work/sdk/c --cxx-sdk /work/sdk/cpp --wrwat /work/sdk/wat/bin/wrwat \
  --vm /work/host/uwvm2-ros --vm-receipt /work/host/receipt.json \
  --vm-target /work/pins/runtime-qualification.json --vm-support /work/vm-support \
  --work /work/results --round-id cfamily-acceptance-01 --jobs 2
```

For the initial x86-64 run add `--profile wasm32-wasip1-noeh-nomte`. To isolate a case, add `--language c|cpp`, `--engine int|aot`, or `--capability source-debug|full-dump-restore|signed-hot-update`. Each filter can be repeated. For a cross-architecture VM, `--runner-json FILE` reads the exact command prefix as a JSON string array. The target process must retain its authenticated direct-parent channel.

## Evidence and verdicts

Each compiler builds the same source twice with `-O0 -g` and its selected width, thread, MTE and EH flags. The runner validates both build receipts and reads the actual Core Wasm sections, including DWARF line, type and string data. It records the public export and the implementation body separately to accommodate linker-generated wrappers. Thread profiles use a bounded shared-memory owner produced by the installed WAT frontend.

- **Source debugging** sets a source breakpoint on the addition, reads `local == 40`, steps to the next marked statement in the original file, reads `local == 42`, and resumes to a checked zero exit.
- **Full restore** stops at an actual Wasm entry, writes four bytes to guest memory, saves a full archive, checks its embedded guest bytes, and overwrites the live word. A positive result requires the old word at the saved Wasm location under a fresh stop after restore, followed by successful execution and exit. The snapshot is kept inside the private results directory. [VM snapshot contract](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/documents/runtime/unified-snapshot.md)
- **Signed hot update** starts a separate VM with debugger permission `none` and a dedicated authenticated update stream. An in-memory, one-use Ed25519 key signs launch, prepare and commit. The same process calls the approved `value()` export on the same channel and nonce, returning 17 at epoch 1 and 29 at epoch 2. Receipts include the installed image hash and the prepared and READY measurements. [VM production update contract](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/documents/runtime/production-update.md)

`inputs.json` records the installed SDK selections, tool digests, round, VM receipt and namespace identities. `build.json` binds both generations to the compiler, source and sysroot. Each capability has its own `result.json` under the profile, language and engine. `results.jsonl` collects the rows. `summary.json` counts positive results and expected negative assertions independently. Retain VM logs, live command records and dumps within the isolated output volume.

`pass` records a positive capability. `expected-rejection` records a successful INT DBG negative assertion with an authenticated descriptor, explicit unsupported diagnostic and exit 126. Both languages and both DBG-dependent operations require independent observations. An INT debugger that accepts a request fails this assertion. The signed-update case always launches independently. `unsupported` records a recognized limitation actually returned by the VM, including a private thread driver's refusal. `restore-declined` records an explicit rejection with the changed original stop and memory retained. `failed` records an unexpected outcome. `build-blocked` means the VM operation could not start. Build failures, unexpected outcomes and restore declines produce a nonzero runner exit. Only `pass` contributes to the positive count.
