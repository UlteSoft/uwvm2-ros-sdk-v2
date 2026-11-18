#define _BSD_SOURCE
#include <string.h>
#include <stddef.h>
#include <stdint.h>

#if !__has_builtin(__builtin_wasm_memtag_claimz) || !__has_builtin(__builtin_wasm_memtag_release)
#if !defined(WROS_LEGACY_MTE)
#error "the strict TinyGo collector requires WebAssembly memory lifetime instructions"
#endif
#define WROS_LEGACY_COLLECTOR 1
#endif

/* Collector metadata holds linear offsets. Object fields and roots retain
   their original tagged pointers for ordinary mutator loads and stores. */
uintptr_t wros_gc_raw(uintptr_t pointer) {
    return (uintptr_t)__builtin_wasm_memtag_untag(0, (void *)pointer);
}

void *wros_gc_tagged(uintptr_t offset) {
    return __builtin_wasm_memtag_load(0, (void *)offset);
}

static void check_granules(uintptr_t offset, size_t bytes) {
    if (!bytes || ((offset | bytes) & 15)) __builtin_trap();
}

void *wros_gc_claim(uintptr_t offset, size_t bytes) {
    check_granules(offset, bytes);
#ifdef WROS_LEGACY_COLLECTOR
    void *pointer = (void *)offset;
    if (__builtin_wasm_memtag_status(0)) {
        do {
            pointer = __builtin_wasm_memtag_random(0, pointer);
        } while (!__builtin_wasm_memtag_extract(0, pointer));
    }
    __builtin_wasm_memtag_storez(0, pointer, bytes);
    return pointer;
#else
    return __builtin_wasm_memtag_claimz(0, (void *)offset, bytes);
#endif
}

void wros_gc_retire(uintptr_t offset, size_t bytes) {
    check_granules(offset, bytes);
#ifdef WROS_LEGACY_COLLECTOR
    __builtin_wasm_memtag_storez(0, (void *)offset, bytes);
#else
    /* The collector owns the complete object while sweeping. Restore the
       tagged base from its shadow and erase the bytes before retiring it. */
    void *pointer = __builtin_wasm_memtag_load(0, (void *)offset);
    explicit_bzero(pointer, bytes);
    (void)__builtin_wasm_memtag_release(0, pointer, bytes);
#endif
}
