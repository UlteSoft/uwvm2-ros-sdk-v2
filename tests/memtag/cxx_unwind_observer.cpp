#include <cstdint>

static std::uintptr_t bases[2];
static unsigned cleaned;

extern "C" void visit_frame(unsigned char *a, unsigned char *b, unsigned round) {
    auto first = (std::uintptr_t)__builtin_wasm_memtag_untag(0, a);
    auto second = (std::uintptr_t)__builtin_wasm_memtag_untag(0, b);
    auto distance = first > second ? first - second : second - first;
    if (distance < 16 || distance - 16 > 64)
        __builtin_trap();
    if (round && (bases[0] != first || bases[1] != second))
        __builtin_trap();
    bases[0] = first;
    bases[1] = second;
    auto tag_a = __builtin_wasm_memtag_extract(0, a);
    auto tag_b = __builtin_wasm_memtag_extract(0, b);
    if (__builtin_wasm_memtag_status(0) ? !tag_a || !tag_b || tag_a == tag_b : tag_a || tag_b)
        __builtin_trap();
    a[15] = 51;
    b[0] = 73;
}

extern "C" void cleanup_frame(unsigned char *a, unsigned char *b) {
    if (a[15] != 51 || b[0] != 73)
        __builtin_trap();
    ++cleaned;
}

extern "C" unsigned cleanup_count() { return cleaned; }
