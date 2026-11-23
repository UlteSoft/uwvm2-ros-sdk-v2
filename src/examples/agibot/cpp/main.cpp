#include <uwrosv2/agibot/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61, 0x6d,
    0x65, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xe0, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xd0, 0xbf,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xfc, 0x3f, 0x01, 0x01
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x66, 0x72, 0x61, 0x6d,
    0x65, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3f, 0xe0, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0xbf, 0xd0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x3f, 0xfc, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        double actual = 0;
        if (!uwrosv2::agibot::read_position(data, size, actual) || actual != 0.5) __builtin_trap();
        if (uwrosv2::agibot::read_position(data, size - 1, actual) || actual != 0.5) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2::agibot::read_velocity(data, size, actual) || actual != -0.25) __builtin_trap();
        if (uwrosv2::agibot::read_velocity(data, size - 1, actual) || actual != -0.25) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2::agibot::read_effort(data, size, actual) || actual != 1.75) __builtin_trap();
        if (uwrosv2::agibot::read_effort(data, size - 1, actual) || actual != 1.75) __builtin_trap();
    }
    {
        uint16_t actual = 0;
        if (!uwrosv2::agibot::read_error_code(data, size, actual) || actual != 257) __builtin_trap();
        if (uwrosv2::agibot::read_error_code(data, size - 1, actual) || actual != 257) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
