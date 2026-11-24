#include <stddef.h>
#include <stdint.h>
#include <string.h>

void vector_compute(uint32_t *restrict out, const uint32_t *restrict left,
                    const uint32_t *restrict right)
{
    for (size_t lane = 0; lane < 64; ++lane)
        out[lane] = (left[lane] + right[lane]) ^ (left[lane] * 33u);
}

void *copy_overlap(void *to, const void *from, size_t size)
{
    return memmove(to, from, size);
}

void *fill_buffer(void *to, int byte, size_t size)
{
    return memset(to, byte, size);
}
