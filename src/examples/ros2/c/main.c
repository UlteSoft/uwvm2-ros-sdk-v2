#include <uwrosv2/ros2/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0xfe, 0xff, 0xff, 0xff, 0x00, 0xa3, 0xe1, 0x11
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xfe, 0x11, 0xe1, 0xa3, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        int32_t actual = 0;
        if (!uwrosv2_ros2_read_sec(data, size, &actual) || actual != -2) __builtin_trap();
        if (uwrosv2_ros2_read_sec(data, size - 1, &actual) || actual != -2) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2_ros2_read_nanosec(data, size, &actual) || actual != 300000000) __builtin_trap();
        if (uwrosv2_ros2_read_nanosec(data, size - 1, &actual) || actual != 300000000) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
