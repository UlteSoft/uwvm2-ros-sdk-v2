#include <uwrosv2/objc/Object.h>
#include <uwrosv2/objc/Capability.h>

@interface ABIReader : UWRObject
- (uint32_t)version;
@end

@implementation ABIReader
- (uint32_t)version {
    return [UWRCapability abi];
}
@end

void _start(void) {
    ABIReader *reader = [ABIReader create];
    if (!reader || [reader version] != 2) __builtin_trap();
    [reader dispose];
}
