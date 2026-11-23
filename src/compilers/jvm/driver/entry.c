#include <stdint.h>
#include <uwrosv2/capability.h>
#include <uwrosv2/clock.h>

static inline int32_t wros_java_scene_abi(void) { return (int32_t)uwrosv2_abi(); }

static inline int32_t wros_java_cap_open(void *alias, int32_t size, void *out) {
    return (int32_t)uwrosv2_raw_capability_open(0, uwrosv2_address(alias), (uint32_t)size, uwrosv2_address(out));
}

static inline int32_t wros_java_cap_close(int64_t handle) {
    return (int32_t)uwrosv2_raw_capability_close((uint64_t)handle);
}

static inline int32_t wros_java_clock_read(int64_t capability, int64_t clock, void *out) {
    uint8_t request[8], length[8] = {0};
    uwrosv2_write_le64(request, (uint64_t)clock);
    uint32_t status = uwrosv2_raw_clock_read((uint64_t)capability, 0, uwrosv2_address(request), 8,
        uwrosv2_address(out), 32, uwrosv2_address(length));
    return status == 0 && uwrosv2_read_le64(length) != 32 ? 22 : (int32_t)status;
}

/* Native imports of the WROS TeaVM collector. Implementations are emitted
   into all.c from core/src/main/resources/org/teavm/backend/c/memory.c. */
extern void *wros_jvm_alloc(int32_t bytes);
extern int32_t wros_jvm_enqueue(void *object);
extern int32_t wros_jvm_marked(void *object);
extern int32_t wros_jvm_freebytes(void);
extern void *wros_jvm_pop(void);
extern void wros_jvm_sweep(void);
extern void wros_jvm_unsupported(void);

static inline void wros_jvm_clear(uint64_t address, int32_t bytes) {
    volatile unsigned char *data = (volatile unsigned char *)(uintptr_t)address;
    for (int32_t index = 0; index < bytes; ++index) data[index] = 0;
}

/* TeaVM emits generic object pointers and forward declarations for Java virtual calls. */
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wincompatible-pointer-types"
#pragma clang diagnostic ignored "-Wdeprecated-non-prototype"
#pragma clang diagnostic ignored "-Wreturn-type"
#include "all.c"
#pragma clang diagnostic pop

extern void __wasm_call_ctors(void);

void _start(void) {
    __wasm_call_ctors();
    if (main(0, 0) != 0) __builtin_trap();
}
