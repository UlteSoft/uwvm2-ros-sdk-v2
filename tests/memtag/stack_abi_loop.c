#include <wros/scene.h>

static volatile unsigned iterations = 32;

void _start(void) {
    unsigned count = iterations;
    for (unsigned i = 0; i < count; ++i) {
        uint64_t handle = 0;
        if (wr_capability_open(0, (uintptr_t)"signal", 6, (uintptr_t)&handle) ||
            !handle || wr_capability_close(handle))
            __builtin_trap();
    }
}
