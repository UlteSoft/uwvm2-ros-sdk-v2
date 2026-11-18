#include <malloc.h>
#include <stdint.h>
#include <stdlib.h>

enum { samples = 48 };
struct extent {
    unsigned char *pointer;
    size_t requested;
    uintptr_t base;
    size_t capacity;
    unsigned tag;
};

static struct extent live[samples];
static unsigned examined;
static int active;

static void examine(unsigned slot, unsigned char *pointer, size_t requested) {
    if (!pointer || requested == 0) __builtin_trap();
    struct extent x = {pointer, requested,
        (uintptr_t)__builtin_wasm_memtag_untag(0, pointer),
        malloc_usable_size(pointer), __builtin_wasm_memtag_extract(0, pointer)};
    if ((x.tag != 0) != active || x.capacity < requested || (x.base | x.capacity) & 15u) __builtin_trap();
    for (unsigned i = 0; i < samples; ++i) {
        if (!live[i].pointer || i == slot) continue;
        struct extent low = x.base < live[i].base ? x : live[i];
        struct extent high = x.base < live[i].base ? live[i] : x;
        if (high.base - low.base < low.capacity) __builtin_trap();
        if (high.base - low.base - low.capacity <= 64) {
            ++examined;
            if (active && low.tag == high.tag) __builtin_trap();
        }
    }
    live[slot] = x;
}

static void retire(unsigned i) {
    struct extent x = live[i];
    free(x.pointer);
    for (size_t n = 0; n < x.capacity; n += 16) {
        void *at = (void *)(x.base + n);
        if (__builtin_wasm_memtag_extract(0, __builtin_wasm_memtag_load(0, at))) __builtin_trap();
    }
    live[i] = (struct extent){0};
}

void _start(void) {
    active = __builtin_wasm_memtag_status(0) != 0;
    for (unsigned pass = 0; pass < 6; ++pass) {
        for (unsigned i = 0; i < samples; ++i) {
            unsigned size = 17 + (i % 3) * 9;
            unsigned char *p;
            switch (i & 3u) {
            case 0: p = malloc(size); break;
            case 1:
                p = calloc(size, 1);
                if (p && (p[0] || p[size - 1])) __builtin_trap();
                break;
            case 2: {
                void *aligned = 0;
                if (posix_memalign(&aligned, 32, size)) __builtin_trap();
                p = aligned;
                if ((uintptr_t)p & 31u) __builtin_trap();
                break;
            }
            default: size = 64;
                p = aligned_alloc(64, size);
                if ((uintptr_t)p & 63u) __builtin_trap();
                break;
            }
            examine(i, p, size);
            p[0] = (unsigned char)(i + 1);
            p[size - 1] = 0x63;
        }
        for (unsigned i = 0; i < samples; i += 2) {
            struct extent old = live[i];
            unsigned char *p = realloc(old.pointer, old.requested + 97);
            if (!p || p[0] != i + 1 || p[old.requested - 1] != 0x63) __builtin_trap();
            examine(i, p, old.requested + 97);
            p = realloc(p, 1);
            if (!p || p[0] != i + 1) __builtin_trap();
            examine(i, p, 1);
        }
        volatile size_t excessive = SIZE_MAX;
        if (realloc(live[1].pointer, excessive) || live[1].pointer[0] != 2) __builtin_trap();
        for (unsigned i = 0; i < samples; ++i) retire((i * 17) % samples);
    }
    if (examined < samples * 6) __builtin_trap();
}
