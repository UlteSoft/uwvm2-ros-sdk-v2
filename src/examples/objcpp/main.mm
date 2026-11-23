#include <uwrosv2/objc/Object.h>
#include <uwrosv2/objc/Capability.h>
#include <array>
#include <numeric>

@interface Reading : UWRObject {
    uint32_t value;
}
- (void)store:(uint32_t)number;
- (uint32_t)load;
@end

@implementation Reading
- (void)store:(uint32_t)number { value = number; }
- (uint32_t)load { return value; }
@end

extern "C" void _start(void) {
    Reading *reading = [Reading create];
    if (!reading) __builtin_trap();
    [reading store:[UWRCapability abi]];
    const std::array<uint32_t, 2> samples = {[reading load], 1};
    const auto sum = std::accumulate(samples.begin(), samples.end(), uint32_t{0});
    [reading dispose];
    if (sum != 3) __builtin_trap();
}
