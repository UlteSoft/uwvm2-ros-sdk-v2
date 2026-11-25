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

## Independently linked C modules sharing one memory

The shared-memory ABI suite builds two C reactors with separate installed `wrc` invocations. Each imports the same bounded `env.memory`. The test reserves the last page beyond both linkers’ minimum memory sizes. It places the public byte, pointer slot and per-module payloads in separate 16-byte-aligned granules. The C functions have no stack objects or static data to coordinate between linkers. A standard Wasm adapter calls the exported functions with the native `i32` or `i64` pointer carrier. [C fixture, adapter and runner](../../src/qualification/cfamily/shared_memory_abi)

- In `raw-offset`, each module independently forms the agreed address of the tag-zero public byte. Both write a distinct value and the other reads it.
- In `pointer-call` and `pointer-slot`, both modules produce pointers. The receiver checks reads and writes through the transferred pointer. Its C pointer addition returns the interior address with the original tag bits. The adapter checks all bits in both directions.
- In `zero-fill`, the receiver seeds the payload and its two adjacent bytes. The producer prepares 16 bytes and the receiver checks every byte and both guards. With runtime checking disabled, the MTE binary returns the raw pointer and `memtag.storez` still clears the payload.
- In `zero-pointer` and `zero-allocation`, a compiler-enabled producer sets a nonzero allocation tag or constructs a nonzero-tagged pointer to the public byte. With checking enabled, both an ordinary read and an ordinary write require exit 122 and the exact pointer, granule and differing tags. With checking disabled, each operation must complete and the peer must observe the expected data.

Run from the SDK checkout with the installed C SDK, including its expanded threaded no-EH sysroots, the VM executable and WABT’s `wat2wasm`. The following command selects one mixed pair in the existing offline qualification harness.

```sh
python3 -I -B src/qualification/cfamily/shared_memory_abi/run.py --isolate \
  --cc-sdk /sdk/c --vm /opt/tools/bin/uwvm2-ros --work .tmp/shared-abi-int32 \
  --width 32 --pair mte-plain --engine int
```

Omit the three selection flags for all four compiler pairs, both widths, both engines and both runtime policies. The full schedule has eight C artifacts and 192 VM processes. Each process executes one case in a fresh instance. `--policy on|off` and `--case` narrow the run further. The isolated run saves each compiler receipt, binary, VM command and log under the work directory’s `results/`. Its `results.jsonl` records every expectation and outcome.
