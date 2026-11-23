// The collector records linear offsets. Application pointers retain their
// allocation tag until the exact complete extent is swept.
typedef __UINTPTR_TYPE__ uptr;
typedef __SIZE_TYPE__ usize;

uptr wros_gc_raw(uptr ptr) {
    return (uptr)__builtin_wasm_memtag_untag(0, (void *)ptr);
}

void *wros_gc_tagged(uptr ptr) {
    return __builtin_wasm_memtag_load(0, (void *)ptr);
}

static void check_extent(uptr base, usize size) {
    if (!size || ((base | size) & 15)) __builtin_trap();
}

void *wros_gc_claim(uptr base, usize size) {
    check_extent(base, size);
    return __builtin_wasm_memtag_claimz(0, (void *)base, size);
}

void wros_gc_retire(uptr base, usize size) {
    check_extent(base, size);
    void *ptr = __builtin_wasm_memtag_load(0, (void *)base);
    volatile unsigned char *bytes = ptr;
    for (usize i = 0; i < size; ++i) bytes[i] = 0;
    (void)__builtin_wasm_memtag_release(0, ptr, size);
}
