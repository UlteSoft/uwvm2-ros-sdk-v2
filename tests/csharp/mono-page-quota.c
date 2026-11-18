#include <stddef.h>
#include <stdint.h>
void *mwpm_alloc_range(size_t, uint8_t);
void mwpm_free_range(void *, size_t);
_Noreturn void mono_assertion_message(const char *p, int line, const char *c) {
    (void)p;
    (void)line;
    (void)c;
    __builtin_trap();
}
void monoeg_g_print(const char *fmt, ...) {
    (void)fmt;
    __builtin_trap();
}
static void require(int condition) {
    if (!condition)
        __builtin_trap();
}
void check_pages(int tagged) {
    if (!!__builtin_wasm_memtag_status(0) != tagged)
        __builtin_trap();
    /* The module's memory maximum, not a simulated allocator, enforces failure. */
    unsigned initial = __builtin_wasm_memory_size(0);
    require(initial == 4);
    require(!mwpm_alloc_range(16u * 65536u, 1));
    require(__builtin_wasm_memory_size(0) == initial);
#ifdef NO_ROOM
    require(!mwpm_alloc_range(65536, 1));
    mwpm_free_range((void *)(uintptr_t)65536, 65536);
    require(!mwpm_alloc_range(65536, 0));
#else
    /* Exactly two extra pages are available. The normal 32-page batch fails;
       the smaller allocation can use one page and the alignment allowance. */
    unsigned char *p = mwpm_alloc_range(65536, 1);
    require(p && !p[0]);
    p[0] = 7;
    mwpm_free_range(p, 65536);
    require(mwpm_alloc_range(65536, 1) == p && !p[0]);
    mwpm_free_range(p, 65536);
#endif
}
