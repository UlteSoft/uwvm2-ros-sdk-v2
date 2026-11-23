#include <uwrosv2/robotis/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x05, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61, 0x6d, 0x65, 0x03, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x97, 0xff, 0xff, 0xff, 0x2c, 0x01, 0x00, 0x00, 0x00, 0x00, 0x44,
    0x41
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint8_t actual = 0;
        if (!uwrosv2::robotis::read_bumper(data, size, actual) || actual != 3) __builtin_trap();
        if (uwrosv2::robotis::read_bumper(data, size - 1, actual) || actual != 3) __builtin_trap();
    }
    {
        int32_t actual = 0;
        if (!uwrosv2::robotis::read_left_encoder(data, size, actual) || actual != -105) __builtin_trap();
        if (uwrosv2::robotis::read_left_encoder(data, size - 1, actual) || actual != -105) __builtin_trap();
    }
    {
        int32_t actual = 0;
        if (!uwrosv2::robotis::read_right_encoder(data, size, actual) || actual != 300) __builtin_trap();
        if (uwrosv2::robotis::read_right_encoder(data, size - 1, actual) || actual != 300) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2::robotis::read_battery(data, size, actual) || actual != 12.25f) __builtin_trap();
        if (uwrosv2::robotis::read_battery(data, size - 1, actual) || actual != 12.25f) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
