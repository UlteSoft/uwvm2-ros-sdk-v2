#include <uwrosv2/nvidia_groot/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3e, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x40, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0xbe,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        float actual = 0;
        if (!uwrosv2_nvidia_groot_read_eef_9d(data, size, 1, &actual) || actual != 0.125f) __builtin_trap();
        if (uwrosv2_nvidia_groot_read_eef_9d(data, size - 1, 1, &actual) || actual != 0.125f) __builtin_trap();
        if (uwrosv2_nvidia_groot_read_eef_9d(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_nvidia_groot_read_gripper_position(data, size, &actual) || actual != 0.75f) __builtin_trap();
        if (uwrosv2_nvidia_groot_read_gripper_position(data, size - 1, &actual) || actual != 0.75f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_nvidia_groot_read_joint_position(data, size, 1, &actual) || actual != -0.25f) __builtin_trap();
        if (uwrosv2_nvidia_groot_read_joint_position(data, size - 1, 1, &actual) || actual != -0.25f) __builtin_trap();
        if (uwrosv2_nvidia_groot_read_joint_position(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
