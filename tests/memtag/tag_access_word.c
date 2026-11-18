#include <stdint.h>

struct __attribute__((packed, may_alias)) word {
    uint32_t value;
};

/* Exercise the raw shadow checked by a straddling access inside a dedicated
   unowned test buffer. Both ends have more than 64 bytes of separation from
   any independently registered neighbor. Stack ownership stays intact. */
_Alignas(16) static unsigned char shadow_test[320] __attribute__((no_sanitize("memtag")));

void check_word(unsigned char *storage, unsigned delta, unsigned store, unsigned cross) {
    const unsigned bits = sizeof(void *) == 4 ? 4 : 8;
    if (__builtin_wasm_memtag_tagbits(0) != bits || delta >= (1u << bits))
        __builtin_trap();
    unsigned tag = __builtin_wasm_memtag_extract(0, storage);
    unsigned char *second = storage + 16;
    void *allocation = __builtin_wasm_memtag_load(0, second);
    if (__builtin_wasm_memtag_extract(0, allocation) != tag)
        __builtin_trap();

    volatile struct word *access;
    if (cross) {
        storage = __builtin_wasm_memtag_insert(0, shadow_test + 128, tag);
        __builtin_wasm_memtag_storez(0, storage, 32);
        second = storage + 16;
        __builtin_wasm_memtag_store(0, __builtin_wasm_memtag_insert(0, second, tag ^ delta), 16);
        access = (volatile struct word *)(storage + 14);
    } else {
        access = __builtin_wasm_memtag_insert(0, second, tag ^ delta);
    }
    if (store)
        access->value = UINT32_C(0x25252525);
    else if (access->value != 0)
        __builtin_trap();

    if (store && storage[16] != 0x25)
        __builtin_trap();
    if (cross)
        __builtin_wasm_memtag_untagstorez(0, storage, 32);
}
