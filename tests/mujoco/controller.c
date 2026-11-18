/* A complete SDK guest for the isolated humanoid test receiver. */
#include <stdint.h>
#include <string.h>
#include <wros/scene.h>
#include "simulation.h"

static uint64_t handle, used;
static uint64_t response[64];

static uint64_t address(const void *p) { return (uintptr_t)p; }
typedef uint32_t operation(uint64_t, uint32_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t);

#ifdef __OBJC__
// All SDK driver operations pass through actual Objective-C message dispatch.
__attribute__((objc_root_class))
@interface JointDriver { Class isa; }
+ (uint32_t)call:(operation *)op input:(const void *)input length:(uint64_t)length;
@end
@implementation JointDriver
+ (uint32_t)call:(operation *)op input:(const void *)input length:(uint64_t)length {
    return op(handle, 0, address(input), length, address(response), sizeof(response), address(&used));
}
@end
static uint32_t invoke(operation *op, const void *input, uint64_t length) {
    return [JointDriver call:op input:input length:length];
}
#else
static uint32_t invoke(operation *op, const void *input, uint64_t length) {
    return op(handle, 0, address(input), length, address(response), sizeof(response), address(&used));
}
#endif

static uint32_t poll(operation *op, const void *input, uint64_t length) {
    for (unsigned attempt = 0; attempt < 10000000; ++attempt) {
        uint32_t status = invoke(op, input, length);
        if (status != 11) return status;
    }
    __builtin_trap();
}

static void check(int ok) { if (!ok) __builtin_trap(); }
#ifdef __cplusplus
extern "C"
#endif
void _start(void) {
    const char alias[] = "joint";
    check(wr_capability_open(0, address(alias), sizeof(alias) - 1, address(&handle)) == 0);
    check(poll(wr_driver_connect, 0, 0) == 0);
    for (uint64_t sequence = 1; sequence <= STEPS; ++sequence) {
        memcpy(request, &sequence, sizeof(sequence));
        memcpy(request + 32, &sequence, sizeof(sequence));
        if (SUCCESS) {
            double target = sequence % 2 ? 0.5 : -0.5;
            memcpy(request + TARGET_OFFSET, &target, sizeof(target));
        }
        check(poll(wr_driver_submit, request, sizeof(request)) == 0);
        uint32_t status = poll(wr_driver_result, &sequence, sizeof(sequence));
        if (CRASH) {
            check(status == 5 || status == 13);
            check(invoke(wr_driver_describe, 0, 0) == 0);
            check(used >= 32 && response[0] == 6 && response[3] == 1);
        } else {
            check(status == 0 && used >= 24 && response[0] == (SUCCESS ? 0 : 13) && response[2] == sequence);
        }
    }
    check(invoke(wr_driver_disconnect, 0, 0) == 0);
}
