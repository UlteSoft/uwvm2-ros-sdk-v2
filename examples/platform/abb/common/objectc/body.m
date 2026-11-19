/** @brief Check the ROSv2 ABI inside the guest and fail on mismatch. */
#include <objc/runtime.h>
#include <wros/scene.h>

__attribute__((objc_root_class))
@interface RobotStatus { Class isa; }
+ (unsigned)hostABI;
@end

@implementation RobotStatus
+ (unsigned)hostABI { return wr_abi(); }
@end

void _start(void) {
    if ([RobotStatus hostABI] != 2) __builtin_trap();
}
