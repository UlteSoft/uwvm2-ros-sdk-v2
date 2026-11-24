#include "probe.h"

template<class Word>
struct VectorInput {
    Word seed;
    Word left_base() const { return seed + Word{17}; }
};

__attribute__((objc_root_class))
@interface IsaInput
+ (uint32_t)leftBase:(uint32_t)seed;
@end

@implementation IsaInput
+ (uint32_t)leftBase:(uint32_t)seed { return VectorInput<uint32_t>{seed}.left_base(); }
@end

int main()
{
    const uint32_t seeds[] = { ISA_SEEDS };
    for (uint32_t seed : seeds)
        if (isa_case(seed, [IsaInput leftBase:seed]))
            return 1;
    return 0;
}
