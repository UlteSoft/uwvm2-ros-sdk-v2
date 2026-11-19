#include "policy.hpp"

#if defined(FIXTURE_EXPECT_EH) != defined(__cpp_exceptions)
#error "unexpected conventional C++ exception mode"
#endif

namespace fixture {
reading forward(unsigned channel) throws { return measure(channel); }

static int check() {
    unsigned caught = 0;
    try {
        auto value = forward(2);
        if (value.value != 44 || value.channel != 2) return 1;
        forward(9);
        return 2;
    } catch throws(std::error error) {
        if (error.domain != &sensor_domain || error.code != 109) return 3;
        ++caught;
    }
    if (caught != 1 || cleanups != 2) return 4;
    auto good = catch return_failure(sample(3));
    if (good.failed || good.value.value != 83 || good.value.channel != 3) return 5;
    auto bad = catch return_failure(sample(11));
    if (!bad.failed || bad.error.code != 711 || bad.error.channel != 11 || cleanups != 4) return 6;
#if defined(FIXTURE_EXPECT_EH)
    try {
        standard_failure();
        return 7;
    } catch (int code) {
        if (code != 31 || cleanups != 5) return 8;
    }
#endif
    return 0;
}
}

#if defined(FIXTURE_NATIVE)
int main() { return fixture::check(); }
#elif defined(FIXTURE_WASM_PARSE)
static_assert(sizeof(void*) * __CHAR_BIT__ == FIXTURE_WIDTH);
extern "C" void _start() { if (fixture::check()) __builtin_trap(); }
#else
static_assert(sizeof(void*) * __CHAR_BIT__ == FIXTURE_WIDTH);
extern "C" void* malloc(word) noexcept;
extern "C" void free(void*) noexcept;
extern "C" void _start() {
    if (fixture::check()) __builtin_trap();
    auto* owner = static_cast<unsigned char*>(malloc(49));
    if (!owner) __builtin_trap();
    auto tag = __builtin_wasm_memtag_extract(0, owner);
    if (!__builtin_wasm_memtag_status(0) || !tag) __builtin_trap();
    for (unsigned i = 0; i < 49; i += 16) {
        void* stored = __builtin_wasm_memtag_load(0, owner + i);
        if (__builtin_wasm_memtag_extract(0, stored) != tag) __builtin_trap();
        static_cast<volatile unsigned char*>(owner)[i] = static_cast<unsigned char>(i);
    }
    free(owner);
}
#endif
