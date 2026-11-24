#include <stddef.h>
#include <stdint.h>
#include <wasi/api.h>

/* Volatile kernel derived from benchmark/0006.memtag/linear_access.c. */
static volatile uint32_t words[1024] __attribute__((aligned(16)));
static volatile uint32_t result __attribute__((aligned(16)));

static __attribute__((noinline)) uint32_t kernel(volatile uint32_t *pool, uint32_t iterations)
{
    for (uint32_t i = 0; i < 1024; ++i)
        pool[i] = i * 17u + 1u;

    uint32_t acc = 0x13579bdfu;
    for (uint32_t i = 0; i < iterations; ++i) {
        uint32_t index = (i * 13u) & 1023u;
        uint32_t value = pool[index];
        acc = (acc << 5) | (acc >> 27);
        acc ^= value + i;
        pool[index] = value + 3u;
    }
    result = acc;
    return result;
}

static char *prefix(char *out, const char *text)
{
    while (*text)
        *out++ = *text++;
    return out;
}

static char *decimal(char *out, uint64_t value)
{
    char reversed[20];
    size_t count = 0;
    do {
        reversed[count++] = (char)('0' + value % 10);
        value /= 10;
    } while (value);
    while (count)
        *out++ = reversed[--count];
    return out;
}

__attribute__((export_name("_start"))) void _start(void)
{
    __wasi_size_t argc, buffer_size;
    uint8_t *argv[2];
    uint8_t arg_buffer[128];
    if (__wasi_args_sizes_get(&argc, &buffer_size) || argc != 2 || buffer_size > sizeof arg_buffer
        || __wasi_args_get(argv, arg_buffer))
        __builtin_trap();

    uint32_t iterations = 0;
    for (const uint8_t *digit = argv[1]; *digit; ++digit) {
        if (*digit < '0' || *digit > '9' || iterations > (UINT32_MAX - 9) / 10)
            __builtin_trap();
        iterations = iterations * 10 + (uint32_t)(*digit - '0');
    }

    volatile uint32_t *pool = words;
    uint32_t matching_tag = 0;
#if __has_builtin(__builtin_wasm_memtag_store)
    if (__builtin_wasm_memtag_status(0)) {
        matching_tag = __builtin_wasm_memtag_extract(0, (void *)pool);
        void *base = __builtin_wasm_memtag_untag(0, (void *)pool);
        void *first = __builtin_wasm_memtag_load(0, base);
        void *last = __builtin_wasm_memtag_load(0, (uint8_t *)base + sizeof words - 16);
        if (matching_tag == 0 || __builtin_wasm_memtag_extract(0, first) != matching_tag
            || __builtin_wasm_memtag_extract(0, last) != matching_tag)
            __builtin_trap();
    }
#endif

    __wasi_timestamp_t before, after;
    if (__wasi_clock_time_get(__WASI_CLOCKID_MONOTONIC, 0, &before))
        __builtin_trap();
    uint32_t checksum = kernel(pool, iterations);
    if (__wasi_clock_time_get(__WASI_CLOCKID_MONOTONIC, 0, &after) || after < before)
        __builtin_trap();

    char buffer[128];
    char *out = prefix(buffer, "linear iterations=");
    out = decimal(out, iterations);
    out = prefix(out, " checksum=");
    out = decimal(out, checksum);
    out = prefix(out, " ns=");
    out = decimal(out, after - before);
    out = prefix(out, " tag=");
    out = decimal(out, matching_tag);
    *out++ = '\n';
    __wasi_ciovec_t iov = {.buf = (const uint8_t *)buffer, .buf_len = (__wasi_size_t)(out - buffer)};
    __wasi_size_t written;
    if (__wasi_fd_write(1, &iov, 1, &written) || written != iov.buf_len)
        __builtin_trap();
}
