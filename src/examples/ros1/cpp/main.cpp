#include <uwrosv2/ros1/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x2d, 0x01, 0x00, 0x00, 0x80, 0x17, 0xb4, 0x2c
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint32_t actual = 0;
        if (!uwrosv2::ros1::read_data_sec(data, size, actual) || actual != 301) __builtin_trap();
        if (uwrosv2::ros1::read_data_sec(data, size - 1, actual) || actual != 301) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2::ros1::read_data_nsec(data, size, actual) || actual != 750000000) __builtin_trap();
        if (uwrosv2::ros1::read_data_nsec(data, size - 1, actual) || actual != 750000000) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
