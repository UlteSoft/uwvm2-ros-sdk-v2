#include <cstddef>
#include <cstdint>
#include <malloc.h>
#include <new>

namespace {
struct object {
    std::uint32_t value;
    unsigned char padding[15];
};
struct alignas(64) aligned_object {
    std::uint32_t value;
};
struct allocation {
    void *pointer;
    std::uintptr_t base;
    std::size_t bytes;
    std::size_t tag;
};
allocation live[32];
}

extern "C" void _start() {
    bool const active = __builtin_wasm_memtag_status(0);
    unsigned compared = 0;
    for (unsigned round = 0; round != 4; ++round) {
        for (unsigned i = 0; i != 32; ++i) {
            // Allocate through both scalar new and aligned array new.
            void *p = i % 4 ? static_cast<void *>(new(std::nothrow) object{i})
                            : static_cast<void *>(new(std::nothrow) aligned_object[2]{{i}, {i + 1}});
            if (!p) __builtin_trap();
            allocation entry{p, (std::uintptr_t)__builtin_wasm_memtag_untag(0, p),
                             malloc_usable_size(p), __builtin_wasm_memtag_extract(0, p)};
            if ((entry.tag != 0) != active || (i % 4 == 0 && entry.base % 64)) __builtin_trap();
            for (unsigned j = 0; j != i; ++j) {
                auto &peer = live[j];
                auto &low = entry.base < peer.base ? entry : peer;
                auto &high = entry.base < peer.base ? peer : entry;
                if (high.base < low.base + low.bytes) __builtin_trap();
                if (high.base - low.base - low.bytes <= 64) {
                    ++compared;
                    if (active && low.tag == high.tag) __builtin_trap();
                }
            }
            live[i] = entry;
        }
        for (unsigned i = 0; i != 32; ++i) {
            auto entry = live[i];
            if (i % 4) {
                auto p = static_cast<object *>(entry.pointer);
                if (p->value != i) __builtin_trap();
                delete p;
            } else {
                auto p = static_cast<aligned_object *>(entry.pointer);
                if (p[0].value != i || p[1].value != i + 1) __builtin_trap();
                delete[] p;
            }
            auto raw = reinterpret_cast<void *>(entry.base);
            if (__builtin_wasm_memtag_extract(0, __builtin_wasm_memtag_load(0, raw))) __builtin_trap();
        }
    }
    if (compared < 64) __builtin_trap();
}
