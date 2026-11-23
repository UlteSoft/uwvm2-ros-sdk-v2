#include <stdint.h>

extern uint32_t wros_main(void);

void _start(void)
{
    if (wros_main() != 0) __builtin_trap();
}
