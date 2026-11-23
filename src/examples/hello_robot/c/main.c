#include <uwrosv2/hello_robot/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x00, 0x00, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x41,
    0x88, 0xff, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x78, 0x56, 0x34, 0x12, 0x00, 0x00, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        float actual = 0;
        if (!uwrosv2_hello_robot_read_ax(data, size, &actual) || actual != 0.5f) __builtin_trap();
        if (uwrosv2_hello_robot_read_ax(data, size - 1, &actual) || actual != 0.5f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_hello_robot_read_az(data, size, &actual) || actual != 9.5f) __builtin_trap();
        if (uwrosv2_hello_robot_read_az(data, size - 1, &actual) || actual != 9.5f) __builtin_trap();
    }
    {
        int16_t actual = 0;
        if (!uwrosv2_hello_robot_read_a0(data, size, &actual) || actual != -120) __builtin_trap();
        if (uwrosv2_hello_robot_read_a0(data, size - 1, &actual) || actual != -120) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2_hello_robot_read_single_tap_count(data, size, &actual) || actual != 513) __builtin_trap();
        if (uwrosv2_hello_robot_read_single_tap_count(data, size - 1, &actual) || actual != 513) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2_hello_robot_read_timestamp(data, size, &actual) || actual != 305419896) __builtin_trap();
        if (uwrosv2_hello_robot_read_timestamp(data, size - 1, &actual) || actual != 305419896) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
