#include <uwrosv2/nvidia/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x06, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00,
    0x78, 0x56, 0x34, 0x12, 0xb1, 0xcb, 0x74, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x05, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x06, 0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00,
    0x12, 0x34, 0x56, 0x78, 0x00, 0x74, 0xcb, 0xb1, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x05
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint32_t actual = 0;
        if (!uwrosv2_nvidia_read_left_ticks(data, size, &actual) || actual != 305419896) __builtin_trap();
        if (uwrosv2_nvidia_read_left_ticks(data, size - 1, &actual) || actual != 305419896) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2_nvidia_read_right_ticks(data, size, &actual) || actual != 7654321) __builtin_trap();
        if (uwrosv2_nvidia_read_right_ticks(data, size - 1, &actual) || actual != 7654321) __builtin_trap();
    }
    {
        uint64_t actual = 0;
        if (!uwrosv2_nvidia_read_encoder_timestamp(data, size, &actual) || actual != UINT64_C(4294967301)) __builtin_trap();
        if (uwrosv2_nvidia_read_encoder_timestamp(data, size - 1, &actual) || actual != UINT64_C(4294967301)) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
