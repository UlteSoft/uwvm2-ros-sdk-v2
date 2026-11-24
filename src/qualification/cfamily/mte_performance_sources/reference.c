#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    uint32_t checksum = UINT32_C(0x13579bdf);
    uint32_t limit = UINT32_C(1) << 27;
    printf("{\"0\":%" PRIu32, checksum);
    for (uint32_t i = 0, target = 1; i < limit; ++i) {
        /* The array repeats every 1024 updates because 13 and 1024 are coprime. */
        uint32_t initial = (i * 13 % 1024) * 17 + 1;
        uint32_t value = initial + (i / 1024) * 3;
        checksum = (checksum * 32 | checksum / (UINT32_C(1) << 27)) ^ (value + i);
        if (i + 1 == target) {
            printf(",\n\"%" PRIu32 "\":%" PRIu32, target, checksum);
            target *= 2;
        }
    }
    puts("}");
    return 0;
}
