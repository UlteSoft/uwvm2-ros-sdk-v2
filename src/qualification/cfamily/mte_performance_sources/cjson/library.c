#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdint.h>
#include "cJSON.h"
#include "payloads.h"

#ifdef __wasm__
#include <wasi/api.h>
#else
#include <stdio.h>
#include <time.h>
#endif

static uint32_t mix(uint32_t hash, uint32_t value)
{
    return (hash ^ value) * UINT32_C(16777619);
}

static uint32_t parse_documents(uint32_t iterations)
{
    uint32_t hash = UINT32_C(2166136261);
    for (uint32_t i = 0; i < iterations; ++i) {
        size_t index = i % (sizeof payloads / sizeof payloads[0]);
        cJSON *root = cJSON_ParseWithLengthOpts(payloads[index], payload_lengths[index] + 1, NULL, 1);
        const cJSON *id = cJSON_GetObjectItemCaseSensitive(root, "id");
        const cJSON *enabled = cJSON_GetObjectItemCaseSensitive(root, "enabled");
        const cJSON *name = cJSON_GetObjectItemCaseSensitive(root, "name");
        const cJSON *values = cJSON_GetObjectItemCaseSensitive(root, "values");
        const cJSON *meta = cJSON_GetObjectItemCaseSensitive(root, "meta");
        if (!cJSON_IsObject(root) || !cJSON_IsNumber(id) || !cJSON_IsBool(enabled)
            || !cJSON_IsString(name) || !cJSON_IsObject(meta) || !cJSON_IsArray(values)
            || cJSON_GetArraySize(values) != 4)
            __builtin_trap();

        hash = mix(hash, (uint32_t)id->valueint);
        hash = mix(hash, (uint32_t)cJSON_IsTrue(enabled));
        for (const unsigned char *byte = (const unsigned char *)name->valuestring; *byte; ++byte)
            hash = mix(hash, *byte);
        hash = mix(hash, 0);
        const cJSON *value;
        cJSON_ArrayForEach(value, values) {
            if (!cJSON_IsNumber(value))
                __builtin_trap();
            hash = mix(hash, (uint32_t)value->valueint);
        }
        cJSON_Delete(root);
    }
    return hash;
}

static uint32_t iterations_from(const char *arg)
{
    uint32_t iterations = 0;
    if (!*arg)
        __builtin_trap();
    for (; *arg; ++arg) {
        if (*arg < '0' || *arg > '9' || iterations > (UINT32_MAX - 9) / 10)
            __builtin_trap();
        iterations = iterations * 10 + (uint32_t)(*arg - '0');
    }
    return iterations;
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

static uint64_t tick(void)
{
#ifdef __wasm__
    __wasi_timestamp_t time;
    if (__wasi_clock_time_get(__WASI_CLOCKID_MONOTONIC, 0, &time))
        __builtin_trap();
    return time;
#else
    struct timespec time;
    if (clock_gettime(CLOCK_MONOTONIC, &time))
        __builtin_trap();
    return (uint64_t)time.tv_sec * UINT64_C(1000000000) + (uint64_t)time.tv_nsec;
#endif
}

static uint32_t matching_tag(void)
{
#if defined(__wasm__) && __has_builtin(__builtin_wasm_memtag_store)
    static volatile uint32_t witness[4] __attribute__((aligned(16)));
    if (__builtin_wasm_memtag_status(0)) {
        void *pointer = (void *)witness;
        uint32_t tag = __builtin_wasm_memtag_extract(0, pointer);
        void *address = __builtin_wasm_memtag_untag(0, pointer);
        void *allocation = __builtin_wasm_memtag_load(0, address);
        if (!tag || __builtin_wasm_memtag_extract(0, allocation) != tag)
            __builtin_trap();
        return tag;
    }
#endif
    return 0;
}

static void benchmark(const char *count)
{
    uint32_t iterations = iterations_from(count);
    uint32_t tag = matching_tag();
    uint64_t before = tick();
    uint32_t checksum = parse_documents(iterations);
    uint64_t after = tick();
    if (after < before)
        __builtin_trap();

    char buffer[128];
    char *out = prefix(buffer, "cjson iterations=");
    out = decimal(out, iterations);
    out = prefix(out, " checksum=");
    out = decimal(out, checksum);
    out = prefix(out, " ns=");
    out = decimal(out, after - before);
    out = prefix(out, " tag=");
    out = decimal(out, tag);
    *out++ = '\n';
#ifdef __wasm__
    __wasi_ciovec_t iov = {.buf = (const uint8_t *)buffer, .buf_len = (__wasi_size_t)(out - buffer)};
    __wasi_size_t written;
    if (__wasi_fd_write(1, &iov, 1, &written) || written != iov.buf_len)
        __builtin_trap();
#else
    size_t length = (size_t)(out - buffer);
    if (fwrite(buffer, 1, length, stdout) != length)
        __builtin_trap();
#endif
}

#ifdef __wasm__
__attribute__((export_name("_start"))) void _start(void)
{
    __wasi_size_t argc, buffer_size;
    uint8_t *argv[2];
    uint8_t arg_buffer[128];
    if (__wasi_args_sizes_get(&argc, &buffer_size) || argc != 2 || buffer_size > sizeof arg_buffer
        || __wasi_args_get(argv, arg_buffer))
        __builtin_trap();
    benchmark((const char *)argv[1]);
}
#else
int main(int argc, char **argv)
{
    if (argc != 2)
        return 2;
    benchmark(argv[1]);
    return 0;
}
#endif
