#include "all.c"
extern void __wasm_call_ctors(void);
void _start(void) {
    __wasm_call_ctors();
    if (main(0, 0)) __builtin_trap();
#ifdef WROS_TEST_HEAP
    if (check_java_owners()<32 || allocated_count < 200) __builtin_trap();
    teavm_gc_collectFull();
    if (reclaimed_count < 200) __builtin_trap();
#endif
}
