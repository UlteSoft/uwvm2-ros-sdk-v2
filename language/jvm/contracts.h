#include <stdint.h>
__attribute__((import_module("uwvm_ros_v2"),import_name("abi"))) extern int abi(void);
extern void *wros_jvm_alloc(int32_t);
extern int32_t wros_jvm_enqueue(void*),wros_jvm_marked(void*), wros_jvm_freebytes(void);
extern void *wros_jvm_pop(void);
extern void wros_jvm_sweep(void);

extern void wros_jvm_unsupported(void);

static inline void wros_jvm_clear(uint64_t address, int32_t count) {
    volatile unsigned char *bytes = (volatile unsigned char *)(uintptr_t)address;
    for (int32_t i = 0; i < count; ++i) bytes[i] = 0;
}
