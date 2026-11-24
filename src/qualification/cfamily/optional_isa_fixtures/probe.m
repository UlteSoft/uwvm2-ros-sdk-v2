#include "probe.h"

__attribute__((objc_root_class))
@interface IsaInput
+ (uint32_t)leftBase:(uint32_t)seed;
@end

@implementation IsaInput
+ (uint32_t)leftBase:(uint32_t)seed { return seed + 17u; }
@end

int main(void)
{
    const uint32_t seeds[] = { ISA_SEEDS };
    for (unsigned i = 0; i < sizeof(seeds) / sizeof(seeds[0]); ++i)
        if (isa_case(seeds[i], [IsaInput leftBase:seeds[i]]))
            return 1;
    return 0;
}
