#include <stdint.h>
#include <limits.h>

static uintptr_t pattern(void) {
    return ((uintptr_t)1 << (sizeof(uintptr_t) * CHAR_BIT - 1)) | 0x2345u;
}

void *sample_address(void) { return (void *)pattern(); }

void check_address(int64_t wide) {
    if ((uint64_t)wide != (uint64_t)pattern()) __builtin_trap();
}

void check_status(int32_t status) {
    if (status != 0) __builtin_trap();
}
