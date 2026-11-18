#include <stdint.h>
#include <stddef.h>

/* The separate translation unit forces the target optimizer to preserve
   the Fortran stack objects and verifies the actual data and pointer ABI. */
void check_samples(const int32_t *samples, int32_t *scalar, int32_t widths,
                   int32_t fast16, int32_t version) {
    if (version != 2 || widths != sizeof(size_t) + sizeof(intptr_t) + sizeof(long)
        || fast16 != sizeof(int_fast16_t) || *scalar != 17) {
        __builtin_trap();
    }
    for (int32_t i = 0; i < 8; ++i) {
        if (samples[i] != (i + 1) * (i + 1) + 2) __builtin_trap();
    }
    *scalar = 23;
}
double sample_value(void) { return 8.0; }
void check_scalar(int32_t value) {
    if (value != 27) __builtin_trap();
}
