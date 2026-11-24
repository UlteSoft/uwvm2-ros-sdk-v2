#include "tag_access.h"
#include <stdlib.h>

#if TEST_MTE
void check_lifecycle(unsigned mode) {
    unsigned char *p = (unsigned char *)malloc(48);
    if (!p)
        __builtin_trap();
    uintptr_t address = (uintptr_t)__builtin_wasm_memtag_untag(0, p);
    unsigned tag = (unsigned)__builtin_wasm_memtag_extract(0, p);
    if (!tag || (address & 15))
        __builtin_trap();
    for (unsigned i = 0; i < 48; i += 16)
        if (shadow_tag(address + i) != tag)
            __builtin_trap();
    write_word(p + 16, UINT32_C(0x25252525));
    if (read_word(p + 16) != UINT32_C(0x25252525))
        __builtin_trap();

    if (mode == 5)
        free(p);
    /* After retirement only the numeric address saved while live goes to
       memtag.load. The instruction reads the separate allocation-tag shadow. */
    unsigned expected = mode == 5 ? 0 : tag;
    for (unsigned i = 0; i < 48; i += 16)
        if (shadow_tag(address + i) != expected)
            __builtin_trap();
    observe(mode, 0, address, tag, shadow_tag(address), shadow_tag(address + 47));
    if (mode == 4)
        free(p);
    completed(0);
}
#endif
