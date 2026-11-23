#include <uwrosv2/yaskawa/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x03, 0x04, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00,
    0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00, 0xfe, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xe8, 0x03, 0x00, 0x00
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x03, 0x00, 0x00, 0x00, 0x06,
    0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x03, 0xe8
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint32_t actual = 0;
        if (!uwrosv2_yaskawa_read_number(data, size, &actual) || actual != 1027) __builtin_trap();
        if (uwrosv2_yaskawa_read_number(data, size - 1, &actual) || actual != 1027) __builtin_trap();
    }
    {
        int32_t actual = 0;
        if (!uwrosv2_yaskawa_read_sub_code(data, size, &actual) || actual != -2) __builtin_trap();
        if (uwrosv2_yaskawa_read_sub_code(data, size - 1, &actual) || actual != -2) __builtin_trap();
    }
    {
        int32_t actual = 0;
        if (!uwrosv2_yaskawa_read_datetime_sec(data, size, &actual) || actual != -1) __builtin_trap();
        if (uwrosv2_yaskawa_read_datetime_sec(data, size - 1, &actual) || actual != -1) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2_yaskawa_read_datetime_nanosec(data, size, &actual) || actual != 1000) __builtin_trap();
        if (uwrosv2_yaskawa_read_datetime_nanosec(data, size - 1, &actual) || actual != 1000) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
