#include "probe.h"

template<class Word>
struct VectorInput {
    Word seed;
    Word left_base() const { return seed + Word{17}; }
};

int main()
{
    const uint32_t seeds[] = { ISA_SEEDS };
    for (uint32_t seed : seeds) {
        const VectorInput<uint32_t> input{seed};
        if (isa_case(input.seed, input.left_base()))
            return 1;
    }
    return 0;
}
