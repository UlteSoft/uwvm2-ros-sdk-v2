#include <stdint.h>

extern uint32_t mix_value(uint32_t);
extern uint32_t mix_slot(volatile uint32_t *);

__attribute__((noinline)) uint32_t bounded_slot(uint32_t x) {
    volatile uint32_t slots[4];
    unsigned index = x & 3U;
    slots[index] = x;
    return mix_value(slots[index]);
}

__attribute__((noinline)) uint32_t escaping_slot(uint32_t x) {
    volatile uint32_t slots[4];
    unsigned index = x & 3U;
    slots[index] = x;
    return mix_slot(&slots[index]);
}

void benchmark(unsigned escaping, unsigned iterations, unsigned low, unsigned high) {
    uint32_t state = 1;
    if (escaping) {
        for (unsigned i = 0; i < iterations; ++i)
            state = escaping_slot(state);
    } else {
        for (unsigned i = 0; i < iterations; ++i)
            state = bounded_slot(state);
    }
    if (state != ((uint32_t)high << 16 | low))
        __builtin_trap();
}

#ifndef __wasm__
#include <stdlib.h>
int main(int argc, char **argv) {
    if (argc != 5)
        return 1;
    benchmark((unsigned)strtoul(argv[1], NULL, 10), (unsigned)strtoul(argv[2], NULL, 10),
              (unsigned)strtoul(argv[3], NULL, 10), (unsigned)strtoul(argv[4], NULL, 10));
    return 0;
}
#endif
