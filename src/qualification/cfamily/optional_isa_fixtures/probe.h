/* Shared workload. Both code generation switches operate on the same source. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifdef __cplusplus
extern "C" {
#endif

enum { ISA_LANES = 64, ISA_BYTES = 64 };
struct IsaStorage {
    uint32_t left[ISA_LANES];
    uint32_t right[ISA_LANES];
    uint32_t result[ISA_LANES];
    unsigned char bytes[ISA_BYTES];
};

/* restrict permits automatic vectorization without alias checks. */
__attribute__((noinline)) void isa_vector(uint32_t *__restrict out,
                                          const uint32_t *__restrict a,
                                          const uint32_t *__restrict b)
{
    for (unsigned i = 0; i < ISA_LANES; ++i)
        out[i] = (a[i] + b[i]) ^ (a[i] * 33u);
}

__attribute__((noinline)) void *isa_move(void *to, const void *from, size_t count)
{
    return memmove(to, from, count);
}

__attribute__((noinline)) void *isa_fill(void *to, int value, size_t count)
{
    return memset(to, value, count);
}

static int output(const void *bytes, size_t count)
{
    const unsigned char *src = (const unsigned char *)bytes;
    while (count) {
        ssize_t n = write(1, src, count);
        if (n <= 0)
            return 0;
        count -= (size_t)n;
        src += n;
    }
    return 1;
}

static int isa_case(uint32_t seed, uint32_t left_base)
{
    /* Observe the allocator and every byte affected by each individual move,
       including guard bytes before and after the destination. */
    struct IsaStorage *s = (struct IsaStorage *)malloc(sizeof(*s));
    if (!s)
        return 1;
    for (unsigned i = 0; i < ISA_LANES; ++i) {
        s->left[i] = left_base + i * 0x9e3779b9u;
        s->right[i] = (seed ^ 0x7f4a7c15u) - i * 0x85ebca6bu;
    }
    isa_vector(s->result, s->left, s->right);
    uint32_t sum = 0;
    for (unsigned i = 0; i < ISA_LANES; ++i)
        sum += s->result[i];
    int ok = output(&seed, sizeof(seed)) && output(s->result, sizeof(s->result)) && output(&sum, sizeof(sum));
    uint32_t state = seed;
    for (unsigned i = 0; i < ISA_BYTES; ++i) {
        state = state * 1664525u + 1013904223u;
        s->bytes[i] = (unsigned char)(state >> 24);
    }
    unsigned delta = 1u + (seed & 7u);
    unsigned length = 24u + ((seed >> 8) & 7u);
    unsigned fill = 2u + ((seed >> 12) & 15u);
    unsigned char *p = s->bytes;
    ok = ok && isa_fill(p + 4, (int)(seed & 255u), fill) == p + 4 && output(p, ISA_BYTES);
    ok = ok && isa_move(p + 8 + delta, p + 8, length) == p + 8 + delta && output(p, ISA_BYTES);
    ok = ok && isa_move(p + 8, p + 8 + delta, length) == p + 8 && output(p, ISA_BYTES);
    ok = ok && isa_move(p + 1, p + ISA_BYTES, 0) == p + 1 && output(p, ISA_BYTES);
    free(s);
    return ok ? 0 : 2;
}

#ifdef __cplusplus
}
#endif
