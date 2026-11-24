#include <stddef.h>
#include <stdint.h>

enum { LANES = 64, BUFFER_SIZE = 64 };

void vector_compute(uint32_t *out, const uint32_t *left, const uint32_t *right);
void *copy_overlap(void *to, const void *from, size_t size);
void *fill_buffer(void *to, int byte, size_t size);

__attribute__((import_module("wasi_snapshot_preview1"), import_name("clock_time_get")))
uint16_t guest_clock_time_get(uint32_t clock, uint64_t precision, uint64_t *time);

#ifdef REPORT_STDOUT
struct GuestIovec {
    const char *bytes;
    uint32_t size;
};

__attribute__((import_module("wasi_snapshot_preview1"), import_name("fd_write")))
uint16_t guest_fd_write(uint32_t fd, const struct GuestIovec *iovecs, uint32_t count, uint32_t *written);

static void report(void)
{
    static const char message[] = "checked vector arithmetic, overlap copy, fill, and WASIp1 clock\n";
    const struct GuestIovec iovec = {message, sizeof(message) - 1};
    uint32_t written;
    if (guest_fd_write(1, &iovec, 1, &written) != 0 || written != iovec.size)
        __builtin_trap();
}
#endif

static void check_vector(void)
{
    uint32_t left[LANES];
    uint32_t right[LANES];
    uint32_t out[LANES];
    for (uint32_t lane = 0; lane < LANES; ++lane) {
        left[lane] = lane * 101u + 2u;
        right[lane] = lane * 31u + 3u;
    }
    vector_compute(out, left, right);
    for (uint32_t lane = 0; lane < LANES; ++lane) {
        uint32_t expected = (lane * 132u + 5u) ^ (lane * 3333u + 66u);
        if (out[lane] != expected)
            __builtin_trap();
    }
}

static void check_buffer(void)
{
    unsigned char bytes[BUFFER_SIZE];
    for (size_t offset = 0; offset < BUFFER_SIZE; ++offset)
        bytes[offset] = (unsigned char)(offset + 1u);

    if (copy_overlap(bytes + 11, bytes + 5, 31) != bytes + 11)
        __builtin_trap();
    if (fill_buffer(bytes + 20, 0xa5, 9) != bytes + 20)
        __builtin_trap();

    for (size_t offset = 0; offset < BUFFER_SIZE; ++offset) {
        unsigned char expected = (unsigned char)(offset + 1u);
        if (offset >= 20 && offset < 29)
            expected = 0xa5;
        else if (offset >= 11 && offset < 42)
            expected = (unsigned char)(offset - 5u);
        if (bytes[offset] != expected)
            __builtin_trap();
    }
}

void _start(void)
{
    uint64_t nanoseconds;
    if (guest_clock_time_get(0, 1, &nanoseconds) != 0 || nanoseconds == 0)
        __builtin_trap();
    check_vector();
    check_buffer();
#ifdef REPORT_STDOUT
    report();
#endif
}
