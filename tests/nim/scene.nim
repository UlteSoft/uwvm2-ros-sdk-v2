import wros_scene
let label = ['s', 'i', 'g', 'n', 'a', 'l']
var handle = new(uint64)
proc sumSamples(n: int): int =
  var samples = newSeq[int](n)
  for i in 0..<n:
    samples[i] = i * i
  for value in samples:
    result += value
doAssert sumSamples(6) == 55
doAssert wr_abi() == 2
let status = wr_capability_open(0, wrAddress(unsafeAddr label[0]), uint64(label.len), wrAddress(addr handle[]))
doAssert status == 0
doAssert wr_capability_close(handle[]) == 0

# Materialize two independent Nim stack objects and a live ARC heap allocation.
# Inspect their tag metadata while all three lifetimes are active.
{.emit: """
#include <stdint.h>
static __attribute__((noinline)) void check_nim_storage(void *p, void *q, void *heap) {
    uintptr_t x = (uintptr_t)__builtin_wasm_memtag_untag(0, p);
    uintptr_t y = (uintptr_t)__builtin_wasm_memtag_untag(0, q);
    if ((x > y ? x-y : y-x) != 16) __builtin_trap();
    if (__builtin_wasm_memtag_status(0)) {
        if (__builtin_wasm_memtag_extract(0, p) == __builtin_wasm_memtag_extract(0, q))
            __builtin_trap();
        void *raw = __builtin_wasm_memtag_untag(0, heap);
        if (__builtin_wasm_memtag_extract(0, heap) !=
            __builtin_wasm_memtag_extract(0, __builtin_wasm_memtag_load(0, raw))) __builtin_trap();
    }
}
""".}
proc checkStorage(p, q, heap: pointer) {.importc: "check_nim_storage", nodecl.}
proc checkFrame(heap: pointer) {.noinline.} =
  var p, q: array[16, uint8]
  checkStorage(addr p, addr q, heap)
checkFrame(addr handle[])
