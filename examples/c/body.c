#include <wros/scene.h>

void _start(void) {
    if (wr_abi() != 2) __builtin_trap();
}
