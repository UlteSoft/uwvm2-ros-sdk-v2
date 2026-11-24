# WasmMTE scalar access conformance

This suite checks a four-byte read and write inside a live, aligned buffer. Each installed compiler parses the same fixture in its own dialect. The guest uses 16-byte tag granules, with four tag bits on wasm32 and eight on wasm64. INT and LLVM AOT run the same linked module with synchronous software tag checking. [Runner](../../src/qualification/cfamily/memtag_suite.py) · [Source fixtures](../../src/qualification/cfamily/memtag_fixtures) · [简体中文](../zh/cfamily-memtag-tests.md)

- **Single granule.** A separately compiled function receives a 48-byte stack object. It verifies the compiler-generated pointer tag against the allocation shadow. It reads or writes bytes 16–19, varying only the logical pointer tag.
- **Two granules.** An aligned 320-byte fixture controls the shadow for bytes 128–159. The four-byte operation starts at byte 142. The first granule matches the pointer and the selected tag difference applies only to the second granule.
- **Allocator.** A live 48-byte allocation has a nonzero tag across three granules and supports an ordinary in-bounds write and read. A separate run saves the numeric base and tag, calls `free`, then queries those three entries in the allocation-tag shadow. Every payload access occurs during the allocation’s lifetime.
- **MTE disabled.** Each read and write runs at both placements with a zero tag difference. The final module must have zero WasmMTE instructions.

## Run from an SDK source checkout

For timing the linear-access kernel under software and hardware tag checking, see the five-host performance guide. [Kernel measurements and replay](cfamily-mte-performance.md)

Supply installed language prefixes, a VM matching the reviewed commit/tree and receipt, the qualification decoder, and an empty output directory on the project volume. The runner creates a bounded shared memory owner for threaded profiles. The decoder uses the vendored WasmMTE instruction definitions. [Decoder sources](../../src/qualification/cfamily/decoder)

```sh
(cd src/qualification/cfamily/decoder && cargo build --release --locked --offline)
python3 -I -B src/qualification/cfamily/memtag_suite.py \
  --cc-sdk /sdk/c --cxx-sdk /sdk/cpp --objc-sdk /sdk/objc --objcpp-sdk /sdk/objcpp \
  --vm /opt/tools/bin/uwvm2-ros \
  --decoder src/qualification/cfamily/decoder/target/release/decode-memtag \
  --work /work/memtag --jobs 4
```

For one cell, add `--language objc --profile wasm64-wasip1-threads-noeh-mte --engine int`. These three filters are repeatable. Supply only the SDK prefixes selected by the language filter. Use `--vm-receipt` and `--vm-target` for separately mounted VM build and revision records. `--compile-timeout` and `--run-timeout` are in seconds.

The default schedule covers a zero difference, every individual tag bit and the all-bits difference. Per host it builds 64 modules and schedules 2,432 VM executions. These comprise 256 ordinary controls, 256 matching-tag accesses, 1,792 deliberate mismatches, 64 live allocator observations and 64 retired-shadow observations. Add `--exhaustive` to exercise all 16 or 256 differences on single-granule accesses.

## Read a result

Before the tested access the guest emits the case number, requested tag difference, untagged byte address, logical tag, first allocation tag and last allocation tag as six little-endian 64-bit integers. Returning from the access emits a four-byte completion value before verification and cleanup. Each mismatch must use the same untagged address as its matching control on that engine. It must exit 122 with the memory-protection diagnostic for the linked scalar function, memory 0, the recorded pointer and the offending granule’s address and tag. The result records the instruction offset when the VM supplies it.

`inputs.json` identifies the inputs and selected workload. Each row in `results.jsonl` has the compiler receipt and guest digests, whole-module instruction counts, the exact decoded `i32.load` and `i32.store` in the access functions, and each invocation’s phase, command and outcome. Raw captures are under the row’s `directory` and `log_prefix`. `summary.json` counts builds, executions and passing observations by phase. Exit 0 requires every selected build and execution to pass.
