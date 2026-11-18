#include <stdint.h>
#include <wros/scene.h>
extern uint32_t d_controller(uint32_t selector);
void _start(void) {if(d_controller(5)!=50) __builtin_trap();}
