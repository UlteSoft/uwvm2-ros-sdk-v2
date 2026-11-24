#include "tag_access.h"

/* The test controls just two granules in the middle of this separate object.
   No managed neighbor is within 64 bytes of either granule. */
static unsigned char shadow_test[320] __attribute__((aligned(16), no_sanitize("memtag")));

void check_word(unsigned char *storage, unsigned mode, unsigned delta) {
    const unsigned cross = mode >> 1, store = mode & 1;
    const unsigned offset = cross ? 14 : 16;
    unsigned char *base = cross ? shadow_test + 128 : storage;
    unsigned char *access = base + offset;
    uintptr_t address = (uintptr_t)access;
    unsigned logical = 0, first = 0, last = 0;
#if TEST_MTE
    const unsigned bits = sizeof(void *) == 4 ? 4 : 8;
    const unsigned tag = (unsigned)__builtin_wasm_memtag_extract(0, storage);
    if (__builtin_wasm_memtag_tagbits(0) != bits || delta >= (1u << bits) || !tag ||
        shadow_tag((uintptr_t)__builtin_wasm_memtag_untag(0, storage + 16)) != tag)
        __builtin_trap();
    if (cross) {
        base = (unsigned char *)__builtin_wasm_memtag_insert(0, base, tag);
        __builtin_wasm_memtag_storez(0, base, 32);
        __builtin_wasm_memtag_store(0, __builtin_wasm_memtag_insert(0, base + 16, tag ^ delta), 16);
        access = base + offset;
    } else {
        access = (unsigned char *)__builtin_wasm_memtag_insert(0, access, tag ^ delta);
    }
    address = (uintptr_t)__builtin_wasm_memtag_untag(0, access);
    if (address != (uintptr_t)__builtin_wasm_memtag_untag(0, base + offset))
        __builtin_trap();
    logical = (unsigned)__builtin_wasm_memtag_extract(0, access);
    first = shadow_tag(address);
    last = shadow_tag(address + 3);
#else
    if (delta)
        __builtin_trap();
#endif
    observe(mode, delta, address, logical, first, last);
    uint32_t value = 0;
    if (store)
        write_word(access, UINT32_C(0x25252525));
    else
        value = read_word(access);
    /* A returned access is visible even if a later check or cleanup traps. */
    completed(value);
    if (value || (store && read_word(base + offset) != UINT32_C(0x25252525)))
        __builtin_trap();
#if TEST_MTE
    if (cross)
        __builtin_wasm_memtag_untagstorez(0, base, 32);
#endif
}
