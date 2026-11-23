#include <uwrosv2/scene.h>

void _start(void) {
    if (uwrosv2_abi() != 2) __builtin_trap();
}
