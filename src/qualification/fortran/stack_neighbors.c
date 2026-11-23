#include <stdint.h>

extern void capture_fortran(uintptr_t *, uintptr_t *, int *);

void inspect_fortran(void) {
    uintptr_t first, second;
    int value;
    capture_fortran(&first, &second, &value);

    /* Compare the saved pointer representations without accessing either
       Fortran object after its lifetime. */
    void *left = (void *)first;
    void *right = (void *)second;
    uintptr_t a = (uintptr_t)__builtin_wasm_memtag_untag(0, left);
    uintptr_t b = (uintptr_t)__builtin_wasm_memtag_untag(0, right);
    uintptr_t gap = a < b ? b - a : a - b;
    if (gap != 16 || value != 42)
        __builtin_trap();
    if (__builtin_wasm_memtag_status(0) &&
        __builtin_wasm_memtag_extract(0, left) == __builtin_wasm_memtag_extract(0, right))
        __builtin_trap();
}
