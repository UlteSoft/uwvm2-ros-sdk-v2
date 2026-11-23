#include <uwrosv2/capability.hpp>

extern "C" void test_abi(uint32_t expected) {
    if (uwrosv2::abi() != expected) __builtin_trap();
}
