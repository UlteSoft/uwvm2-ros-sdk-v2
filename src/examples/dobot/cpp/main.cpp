#include <uwrosv2/dobot/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x00, 0x01
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x01
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        bool actual = 0;
        if (!uwrosv2::dobot::read_is_enable(data, size, actual) || actual != 0) __builtin_trap();
        if (uwrosv2::dobot::read_is_enable(data, size - 1, actual) || actual != 0) __builtin_trap();
    }
    {
        bool actual = 0;
        if (!uwrosv2::dobot::read_is_connected(data, size, actual) || actual != 1) __builtin_trap();
        if (uwrosv2::dobot::read_is_connected(data, size - 1, actual) || actual != 1) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
