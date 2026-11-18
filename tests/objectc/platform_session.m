#include <objc/runtime.h>
#include <stdint.h>
#include <wros/scene.h>

__attribute__((objc_root_class))
@interface DriverSession { Class isa; }
+ (unsigned)connect:(uint64_t)token response:(uint64_t *)reply length:(uint64_t *)written;
+ (unsigned)disconnect:(uint64_t)token response:(uint64_t *)reply length:(uint64_t *)written;
@end
@implementation DriverSession
+ (unsigned)connect:(uint64_t)token response:(uint64_t *)reply length:(uint64_t *)written {
    return wr_driver_connect(token, 0, 0, 0, (uintptr_t)reply, sizeof(*reply), (uintptr_t)written);
}
+ (unsigned)disconnect:(uint64_t)token response:(uint64_t *)reply length:(uint64_t *)written {
    return wr_driver_disconnect(token, 0, 0, 0, (uintptr_t)reply, sizeof(*reply), (uintptr_t)written);
}
@end

void _start(void) {
    char alias[] = "arm";
    uint64_t token=0, reply=17185, written=4660;
    if (wr_capability_open(0, (uintptr_t)alias, 3, (uintptr_t)&token) != 0) __builtin_trap();
#if EXPECT_DENIAL
    if ([DriverSession connect:token response:&reply length:&written] != 13 ||
        reply != 17185 || written != 4660) __builtin_trap();
#else
    unsigned status=11;
    for (unsigned i=0; status == 11 && i < 10000000; ++i)
        status=[DriverSession connect:token response:&reply length:&written];
    if (status != 0 || written != sizeof(reply)) __builtin_trap();
    if ([DriverSession disconnect:token response:&reply length:&written] != 0) __builtin_trap();
#endif
}
