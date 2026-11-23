#include <uwrosv2/ros/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xe0, 0x3f,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xe0, 0xbf, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xe0, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xe0, 0x3f
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0x3f, 0xe0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xbf, 0xe0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3f, 0xe0, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x3f, 0xe0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        double actual = 0;
        if (!uwrosv2::ros::read_x(data, size, actual) || actual != 0.5) __builtin_trap();
        if (uwrosv2::ros::read_x(data, size - 1, actual) || actual != 0.5) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2::ros::read_y(data, size, actual) || actual != -0.5) __builtin_trap();
        if (uwrosv2::ros::read_y(data, size - 1, actual) || actual != -0.5) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2::ros::read_z(data, size, actual) || actual != 0.5) __builtin_trap();
        if (uwrosv2::ros::read_z(data, size - 1, actual) || actual != 0.5) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2::ros::read_w(data, size, actual) || actual != 0.5) __builtin_trap();
        if (uwrosv2::ros::read_w(data, size - 1, actual) || actual != 0.5) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
    check_frame(example + 4, sizeof example - 4);
}
