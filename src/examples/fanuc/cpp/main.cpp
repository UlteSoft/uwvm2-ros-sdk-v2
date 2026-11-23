#include <uwrosv2/fanuc/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x20, 0xc0, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x04, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xbe, 0x02, 0x00, 0x00, 0x00
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0xc0, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x41, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xbe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        float actual = 0;
        if (!uwrosv2::fanuc::read_force_x(data, size, actual) || actual != -2.5f) __builtin_trap();
        if (uwrosv2::fanuc::read_force_x(data, size - 1, actual) || actual != -2.5f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2::fanuc::read_force_z(data, size, actual) || actual != 8.25f) __builtin_trap();
        if (uwrosv2::fanuc::read_force_z(data, size - 1, actual) || actual != 8.25f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2::fanuc::read_moment_z(data, size, actual) || actual != -0.125f) __builtin_trap();
        if (uwrosv2::fanuc::read_moment_z(data, size - 1, actual) || actual != -0.125f) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2::fanuc::read_fs_type(data, size, actual) || actual != 2) __builtin_trap();
        if (uwrosv2::fanuc::read_fs_type(data, size - 1, actual) || actual != 2) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
