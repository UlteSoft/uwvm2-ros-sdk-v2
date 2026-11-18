# WasmMTE detection guarantees

Development frontends with a supported MTE profile enable instrumentation by default. Users can select a complete uninstrumented target and its matching sysroot. Source attributes can change local instrumentation. A review should distinguish the target profile, a source author's explicit attribute and a compiler optimization.

## Tag comparisons

The SDK's WasmMTE software backend uses 16-byte granules. A wasm32 pointer has four tag bits and a wasm64 pointer has eight. In synchronous mode, an ordinary access checks every granule it touches. A single mismatch must reject the access. Under the legacy independently sampled allocation policy, adjacent allocations can have equal tags. A subobject overrun inside a granule can also pass the comparison.

Given a fixed tag and an independent uniform draw from all encodings, the probability of a mismatch is 15/16 for wasm32 and 255/256 for wasm64. Repeating an access with the same stale pointer and allocation does not draw another tag. The libc heap reserves zero for allocator metadata and retired storage. Two independently drawn live heap tags differ with probability 14/15 and 254/255 respectively. Between retirement and reuse, a stale nonzero tag always differs from the cleared granule. None of these probabilities estimates the fraction of bugs caught in an application.

## Managed allocation policy

The VM selects each allocation color in the directory of its backing linear memory. Two distinct live or reserved extents must have different colors whenever there are at most 64 bytes between their 16-byte granule ranges. This includes contiguous allocations, a short allocator header and imported aliases of the same memory. The allocator excludes every neighbor on both sides. The hardware path also excludes all encodings with a conflicting physical low nibble. Zero represents unowned backing storage. A failed reservation publishes no pointer or color.

| What the compiler can establish | How the target handles it |
| --- | --- |
| The value lives entirely in registers | There is no linear-memory object to tag. |
| Two pointers alias one live object | Preserve the tag through pointer derivation and interoperation. |
| Two distinct objects must coexist and their final layout places them nearby | Retain both owners. Before a pointer escapes, reserve or publish its color. An access whose bounds or lifetime remain uncertain still needs checks. |
| Relative addresses depend on linking, allocation, imports or scheduling | Resolve the backing owner and actual extents at runtime. Exclude every near color, then sample from the remaining palette. |

Source declaration order alone does not establish stack or linker layout. Memory released and reacquired at the same address also creates a new lifetime. Spatial exclusion by itself gives no permanent generation identifier.

At this radius the two edges expose at most ten external granules. A closed allocation on either side occupies at least one granule. This bounds the number of simultaneous nearby managed objects even for variable-size, independently released allocations.

The selector draws uniformly from the remaining legal colors. At fixed exclusions this gives the largest possible entropy. A multiplication and rejection step removes incomplete buckets, including when the palette size does not divide 65,536. Distant regions may reuse a color. The 15/16 and 255/256 figures above describe the independent, full-domain experiment. They do not describe a near-neighbor guarantee or the probability of detecting an arbitrary program error. [Lemire, Fast Random Integer Generation in an Interval](https://arxiv.org/abs/1805.10941)

A frontend, language allocator or interpreter must register each independently protected extent. The release qualification applies to a specific producer, runtime library, VM and target combination. A custom arena or a materialized subobject sharing one granule needs an explicit layout or finer bounds checks. A build of the interpreter as Wasm can protect its linear memory while leaving separate guest-language objects in a shared arena. These cases require separate runtime evidence.

## Thread-local objects

The Wasm linker checks the final set of live TLS symbols after archive extraction, dead-code removal and link-time optimization. The current threaded libc can place TLS inside a heap allocation or a caller-provided stack. Strict linking rejects a multithreaded image containing live, tagged TLS data until the runtime can register and retire each object for every thread exit path. A failure names the affected symbol. A relocatable link preserves that information for the final link. The standalone linker accepts the explicit `--allow-legacy-tagged-tls` option for an older allocation policy. Such a build does not qualify for managed-neighbor guarantees.

## Conditions for automatic tag elision

For a stack allocation, the compiler needs proof that every reachable access through its address and derived pointers is within the allocation's bounds and its corresponding lifetime. The condition also applies across calls that receive the address. Unresolved indices, call targets or escapes require instrumentation. Omitting the allocation color additionally requires proof that accesses originating elsewhere cannot enter its storage without a separate bounds or lifetime check. An object that has been promoted entirely to registers has no remaining linear-memory access to protect. An explicit source opt-out records an author's decision. It does not establish an optimization proof.

## Reproducing the checks

Run the following acceptance suites with the rebuilt toolchain and VM inside the 64 GiB qualification cgroup. Each accepts `--toolchain PREFIX --runtime VM --work NEW_DIRECTORY`. Use a different directory under the SDK's `.tmp` for each invocation.

- `tests/memtag_stack_generations.py` exercises loops, early pointer publication, and 17 or 257 simultaneously live stack objects. It checks the tags of actual neighbors after compiler layout.
- `tests/memtag_global_pointer_origins.py` links two translation units. A legal one-past pointer for one array and the base of the next array have the same numerical address. The test verifies both tags, interior pointers, and in-bounds reads and writes through the owning arrays.

Both suites execute the same guest with tagging on and off under the interpreter and AOT engine, for wasm32 and wasm64. Their local results record the exact tool and module digests.
