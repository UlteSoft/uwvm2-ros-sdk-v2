#include <stdint.h>

uint32_t mix_value(uint32_t value) {
    return value * UINT32_C(1664525) + UINT32_C(1013904223);
}

uint32_t mix_slot(volatile uint32_t *slot) {
    return *slot * UINT32_C(1664525) + UINT32_C(1013904223);
}
