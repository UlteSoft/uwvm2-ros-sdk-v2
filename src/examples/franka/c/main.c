#include <uwrosv2/franka/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf2, 0x3f,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0xbf, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xe8, 0xbf, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0x3f,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xd0, 0x3f, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xf0, 0xbf, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa0, 0x3f,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xb0, 0xbf, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xc0, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xd0, 0xbf
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0x3f, 0xf2, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xbf, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xbf, 0xe8, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x3f, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x3f, 0xd0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xbf, 0xf0, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x3f, 0xa0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xbf, 0xb0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3f, 0xc0, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0xbf, 0xd0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        double actual = 0;
        if (!uwrosv2_franka_read_position(data, size, 1, &actual) || actual != -1.0) __builtin_trap();
        if (uwrosv2_franka_read_position(data, size - 1, 1, &actual) || actual != -1.0) __builtin_trap();
        if (uwrosv2_franka_read_position(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2_franka_read_desired_position(data, size, 1, &actual) || actual != 1.0) __builtin_trap();
        if (uwrosv2_franka_read_desired_position(data, size - 1, 1, &actual) || actual != 1.0) __builtin_trap();
        if (uwrosv2_franka_read_desired_position(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2_franka_read_commanded_position(data, size, 1, &actual) || actual != -1.0) __builtin_trap();
        if (uwrosv2_franka_read_commanded_position(data, size - 1, 1, &actual) || actual != -1.0) __builtin_trap();
        if (uwrosv2_franka_read_commanded_position(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2_franka_read_commanded_velocity(data, size, 1, &actual) || actual != -0.0625) __builtin_trap();
        if (uwrosv2_franka_read_commanded_velocity(data, size - 1, 1, &actual) || actual != -0.0625) __builtin_trap();
        if (uwrosv2_franka_read_commanded_velocity(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2_franka_read_commanded_acceleration(data, size, 1, &actual) || actual != -0.25) __builtin_trap();
        if (uwrosv2_franka_read_commanded_acceleration(data, size - 1, 1, &actual) || actual != -0.25) __builtin_trap();
        if (uwrosv2_franka_read_commanded_acceleration(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
