#define _POSIX_C_SOURCE 200809L
#include "guest.h"
#include <lz4.h>
#include <string.h>

enum { block_size = 16384, blocks = 16, rounds = 32 };
static char input[blocks][block_size], decoded[blocks][block_size];
static char compressed[LZ4_COMPRESSBOUND(block_size)];

static __attribute__((noinline)) void round_trip(unsigned count)
{
    for (unsigned pass = 0; pass < count; ++pass) {
        for (unsigned block = 0; block < blocks; ++block) {
            int size = LZ4_compress_default(input[block], compressed, block_size, sizeof compressed);
            if (size <= 0 || LZ4_decompress_safe(compressed, decoded[block], size, block_size) != block_size)
                abort();
        }
    }
}

int main(void)
{
    bench_report_mode();
    for (unsigned block = 0; block < blocks; ++block)
        for (unsigned i = 0; i < block_size; ++i)
            input[block][i] = (char)(i % 71 + block + ((i >> 8) & 15));
    round_trip(1);
    if (memcmp(input, decoded, sizeof input))
        abort();
    uint64_t start = bench_tick();
    round_trip(rounds);
    uint64_t end = bench_tick();
    if (memcmp(input, decoded, sizeof input))
        abort();
    uint64_t checksum = UINT64_C(14695981039346656037);
    for (unsigned block = 0; block < blocks; ++block)
        for (unsigned i = 0; i < block_size; ++i)
            checksum = (checksum ^ (unsigned char)decoded[block][i]) * UINT64_C(1099511628211);
    bench_result("c workload=lz4", (uint64_t)rounds * sizeof input, checksum, start, end);
    return 0;
}
