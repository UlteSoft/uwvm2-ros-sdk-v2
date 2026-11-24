#include "probe.h"

int main(void)
{
    const uint32_t seeds[] = { ISA_SEEDS };
    for (unsigned i = 0; i < sizeof(seeds) / sizeof(seeds[0]); ++i)
        if (isa_case(seeds[i], seeds[i] + 17u))
            return 1;
    return 0;
}
