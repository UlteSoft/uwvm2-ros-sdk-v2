#include <uwrosv2/capability.h>

void test_abi(uint32_t expected) {
    if (uwrosv2_abi() != expected) __builtin_trap();
}
