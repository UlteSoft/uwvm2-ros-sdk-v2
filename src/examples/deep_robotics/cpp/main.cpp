#include <uwrosv2/deep_robotics/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x80, 0x3e, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x40, 0xbf, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xc0, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x18, 0x41
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0x3e, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xbf, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x3f, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x41, 0x18, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        float actual = 0;
        if (!uwrosv2::deep_robotics::read_roll(data, size, actual) || actual != 0.25f) __builtin_trap();
        if (uwrosv2::deep_robotics::read_roll(data, size - 1, actual) || actual != 0.25f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2::deep_robotics::read_yaw(data, size, actual) || actual != -0.75f) __builtin_trap();
        if (uwrosv2::deep_robotics::read_yaw(data, size - 1, actual) || actual != -0.75f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2::deep_robotics::read_omega_z(data, size, actual) || actual != 1.5f) __builtin_trap();
        if (uwrosv2::deep_robotics::read_omega_z(data, size - 1, actual) || actual != 1.5f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2::deep_robotics::read_acc_z(data, size, actual) || actual != 9.5f) __builtin_trap();
        if (uwrosv2::deep_robotics::read_acc_z(data, size - 1, actual) || actual != 9.5f) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
