/* Observe the allocator's public payload and separate tag shadow. No byte
   of a retired allocation is read. The wasm builtins query memory 0. */
#include <__macro_PAGESIZE.h>
#include <stdint.h>
#include <stdlib.h>

static unsigned allocation_tag(uintptr_t address) {
    return __builtin_wasm_memtag_extract(0, __builtin_wasm_memtag_load(0, (void *)address));
}

static void expect_shadow(uintptr_t address, unsigned bytes, unsigned tag) {
    for (unsigned i = 0; i < bytes; i += 16)
        if (allocation_tag(address + i) != tag)
            __builtin_trap();
    if (allocation_tag(address + bytes - 1) != tag)
        __builtin_trap();
}

static unsigned check_active(unsigned char *ptr, unsigned bytes) {
    if (!ptr)
        __builtin_trap();
    unsigned tag = __builtin_wasm_memtag_extract(0, ptr);
    if (!tag)
        __builtin_trap();
    expect_shadow((uintptr_t)__builtin_wasm_memtag_untag(0, ptr), bytes, tag);
    return tag;
}

/* The SDK uses standard 64 KiB pages. This is the absolute value supplied
   by wasm-ld even if that number is also the address of a tagged global. */
__attribute__((noinline)) uintptr_t page_size_constant(void) {
    return PAGESIZE;
}

void check_lifecycle(void) {
    if (page_size_constant() != 65536)
        __builtin_trap();
    for (unsigned n = 1; n <= 257; n += 16) {
        unsigned char *buffer = calloc(n, 1);
        check_active(buffer, n);
        for (unsigned i = 0; i < n; ++i) {
            if (buffer[i] != 0)
                __builtin_trap();
            buffer[i] = (unsigned char)(n + i);
        }
        unsigned char *other = malloc(37);
        check_active(other, 37);
        other[36] = 42;
        buffer = realloc(buffer, n + 95);
        check_active(buffer, n + 95);
        for (unsigned i = 0; i < n; ++i)
            if (buffer[i] != (unsigned char)(n + i))
                __builtin_trap();
        if (other[36] != 42)
            __builtin_trap();
        uintptr_t retired = (uintptr_t)__builtin_wasm_memtag_untag(0, buffer);
        free(buffer);
        expect_shadow(retired, n + 95, 0);
        check_active(other, 37);
        retired = (uintptr_t)__builtin_wasm_memtag_untag(0, other);
        free(other);
        expect_shadow(retired, 37, 0);
    }
}
