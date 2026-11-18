# Stable WasmMTE producer and rebuild contract

This directory builds the pinned LLVM 23.1.5 WebAssembly producer and WASI SDK 34
library sources recorded in `source-lock.json`. WasmMTE is a nonstandard
instruction extension; selecting Wasm Core 3.0 does not make it part of that
standard. The producer registers only WebAssembly targets and defaults to
`wasm32-wasip1-threads`.

The SDK profile driver in `install/compiler.py` selects address width, Core
version, threads, MTE and exception support independently. A matching sysroot
must exist for the complete profile. It never substitutes a host library,
another compiler's sysroot, memory32 for memory64, or an uninstrumented runtime.
A completed build receipt is not deployment or memory-safety qualification.

## Selecting instrumentation

The SDK defaults to memory tagging. An application can select a complete
non-MTE target profile explicitly. Within an instrumented C or C++ translation
unit, Clang honors standard `no_sanitize("memtag")` annotations. Their scope is
the annotated declaration. A neighboring function still receives the target's
normal instrumentation when it needs a runtime check. Selecting a different
profile requires matching guest libraries and separate qualification.

The producer build uses Clang and FileCheck on the generated wasm32 and wasm64
assembly for both C and C++. It checks an annotated function alongside a
normally tagged function and repeats the check with MTE disabled for the whole
translation unit. Guest libraries, import permissions and VM enforcement have
separate acceptance tests.

## Proof-based tag elision

The strict stack pass promotes eligible function-local values to SSA registers.
An object that still has an address in linear memory keeps its own allocation
record, even if the compiler can prove that accesses through its local pointer
stay in bounds. Such a proof says nothing about accesses through pointers to
other live objects. Two aliases of one object carry the same tag.

The compiler claims a fixed-size object when it becomes live and releases the
exact extent at retirement. When its address has to be published earlier, a
reservation holds the tag until activation. The compiler carries active pointers
along control-flow edges. An escaped pointer keeps the tag of the lifetime in
which it was issued. Strict stack lowering diagnoses unsupported dynamic sizes
and escaping nonlocal exits.

At allocation time the VM checks the final layout of the backing memory. In
the managed profile, distinct live or reserved extents separated by up to and
including 64 bytes must differ in tag. The VM chooses uniformly from the colors
still available after checking both sides. Zero marks unowned storage. Wasm32
has 15 nonzero colors and software wasm64 has 255. Physical four-bit checks
also require different low nibbles. Distant allocations and successive uses of
an address can share a tag. Subobjects sharing a granule need additional layout
or bounds protection. Language runtimes that allocate many objects in a single
pool need to register the separate objects for this guarantee to apply.

Run `tests/memtag_stack_generations.py --toolchain <directory> --runtime <vm>
--work <new-directory>` in the qualification cgroup to exercise this lowering.
It checks 17 simultaneously live allocations on wasm32 and 257 on wasm64,
loop re-entry, merged control flow, and pointers published before lifetime
start. Both VM engines run the same module with tagging enabled and disabled.
The observer compares retired pointers as values and checks memory through
the currently live pointer.

The producer build checks both address widths with LLVM's instruction selector,
assembler, and FileCheck. It verifies actual typed operands and machine encoding
for allocation instructions, retained instrumentation on addressable stack
objects, register promotion, and the diagnostics for unsupported storage.
Additional cases distinguish a complete zero initializer from partial or
volatile stores, runtime lengths, and intervening calls. Reproduce these
checks with `check_stack_tagging.py --tool-bin <producer-bin> --source
<prepared-llvm-source> --work <evidence-directory>`.
The prepared source must retain the inventory written by the source build.

For a threaded final link, Wasm LLD rejects live tagged TLS objects while
the guest runtime lacks a dedicated per-thread allocation and retirement
contract. A relocatable link preserves the symbol flags for the final check.
The explicit standalone linker option `--allow-legacy-tagged-tls` selects the
older TLS policy. The Wasm-only tool build includes the Wasm linker driver.

## Rebuild order after a producer change

1. Freeze the previous producer, source hashes, profile descriptions, artifacts
   and performance evidence. Reusing a compiler pathname is not an identity.
2. Build the stable producer from the locked archive and patches with
   `build_producer.py`. Reuse an explicitly supplied native bootstrap toolchain.
3. Use `build_sysroots.py` to rebuild compiler-rt, libc/CRT, libc++, libc++abi and
   libunwind for every supported profile. The component cache key includes the
   producer bytes, recipes, source revisions and patches, and profile options.
4. Rebuild every language's standard library, allocator, runtime, FFI bridge and
   interpreter with that producer/profile before rebuilding SDK examples.
   Relinking an old interpreter or tagging only an application's final object
   is not a complete MTE rebuild. Build-time native source generators may be
   reused when their exact identity is verified; guest runtime objects may not.
5. Execute the language and platform tests through uwvm2-ros. Record failures,
   unsupported combinations, permission-denial cases, and source/import checks.
   An unavailable compiler or runtime does not count as a passing test.
6. Compare native x86_64 runs with VTune hardware hotspots and microarchitecture
   data, retaining source/assembly mappings and checksums. Compare uninstrumented
   programs, instrumented programs with runtime MTE disabled, and enabled MTE
   modes separately. QEMU runs establish architecture correctness, not native
   performance. Preserve mismatch and observed tag-collision counts separately.

The rebuild is incomplete while any selected language or platform lacks its
new runtime or execution evidence. No old qualification transfers merely
because the replacement output has the same filename or ABI.

## Current source-build entry points

- `build_producer.py --work <new-work> --bootstrap <existing-native-prefix>`
- `build_sysroots.py --work <new-work> --toolchain <producer-prefix>`

Language runtime build scripts from the previous SDK still need migration into
this repository; their paths are not installed development entry points here.

The sysroot recipe builds optimized libraries with full debug information.
Locked diagnostic patches are applied in a private source overlay, leaving the
producer's verified LLVM tree unchanged. The overlay copies only patch targets
and their ancestor directories; other paths reference the verified tree. Its
file/link inventory is checked before reuse. libc, libc++abi, libc++ and unwind
assertions remain fatal, while their internal diagnostics do not implicitly
import descriptor I/O or environment-driven tracing. The patches and effective
flags are part of each build receipt and its cache identity. This does not
authorize application filesystem, socket, or logging operations.

The sysroot builder currently admits wasm32 single-thread, wasm32 WASI threads,
and wasm64 single-thread profiles. Memory64 threads require further VM and
startup ABI work and are rejected explicitly. The installer catalog retains
unqualified language/profile combinations as pending; these entry points do
not establish that every SDK language or vendor integration has been rebuilt.

All local test evidence and intermediate builds belong in the appropriate
project's `.tmp` directory. Retain the configured memory/swap controller and
reuse installed build and profiling tools.
