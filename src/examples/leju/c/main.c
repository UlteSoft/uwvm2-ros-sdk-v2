#include <uwrosv2/leju/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x6e, 0xbe, 0x00, 0x00, 0xcc, 0xf7, 0xff, 0xff, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xfd, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint32_t actual = 0;
        if (!uwrosv2_leju_read_voltage(data, size, &actual) || actual != 48750) __builtin_trap();
        if (uwrosv2_leju_read_voltage(data, size - 1, &actual) || actual != 48750) __builtin_trap();
    }
    {
        int32_t actual = 0;
        if (!uwrosv2_leju_read_current(data, size, &actual) || actual != -2100) __builtin_trap();
        if (uwrosv2_leju_read_current(data, size - 1, &actual) || actual != -2100) __builtin_trap();
    }
    {
        uint8_t actual = 0;
        if (!uwrosv2_leju_read_percentage(data, size, &actual) || actual != 65) __builtin_trap();
        if (uwrosv2_leju_read_percentage(data, size - 1, &actual) || actual != 65) __builtin_trap();
    }
    {
        int16_t actual = 0;
        if (!uwrosv2_leju_read_temperatures(data, size, 1, &actual) || actual != -3) __builtin_trap();
        if (uwrosv2_leju_read_temperatures(data, size - 1, 1, &actual) || actual != -3) __builtin_trap();
        if (uwrosv2_leju_read_temperatures(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
