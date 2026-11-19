// This test replaces only the entry of the same generated TeaVM translation
// unit. The ordinary guest runs separately without these observation hooks.
#include "all.c"
extern void __wasm_call_ctors(void);

void _start(void) {
    __wasm_call_ctors();
    if (main(0, 0) || allocated_count < 480 || check_java_owners() < 32)
        __builtin_trap();

    // The generated application has finished. Its object graph may now be
    // reclaimed. Add one known, otherwise unrooted, multi-granule owner.
    const unsigned bytes = 67;
    void *owner = wros_jvm_alloc(bytes);
    if (!owner) __builtin_trap();
    uintptr_t offset = physical(owner);
    unsigned tag = __builtin_wasm_memtag_extract(0, owner);
    if (!!tag != !!__builtin_wasm_memtag_status(0)) __builtin_trap();
    for (unsigned i = 0; i < bytes; i += 16) {
        void *backing = __builtin_wasm_memtag_load(0, (void *)(offset + i));
        if (__builtin_wasm_memtag_extract(0, backing) != tag) __builtin_trap();
        ((volatile unsigned char *)owner)[i] = (unsigned char)(i + 1);
    }
    teavm_gc_collectFull();
    if (reclaimed_count < 480) __builtin_trap();
    for (unsigned i = 0; i < bytes; i += 16) {
        void *retired = __builtin_wasm_memtag_load(0, (void *)(offset + i));
        if (__builtin_wasm_memtag_extract(0, retired)) __builtin_trap();
    }
    volatile unsigned char *fresh = wros_jvm_alloc(bytes);
    if (!fresh) __builtin_trap();
    for (unsigned i = 0; i < bytes; ++i) if (fresh[i]) __builtin_trap();
}
