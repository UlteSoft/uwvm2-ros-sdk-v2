#include <uwrosv2/boston_dynamics/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xbf, 0x00, 0x00, 0xa0, 0x3f, 0x00, 0x00, 0x40, 0x3f
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        float actual = 0;
        if (!uwrosv2_boston_dynamics_read_x(data, size, 1, &actual) || actual != -0.5f) __builtin_trap();
        if (uwrosv2_boston_dynamics_read_x(data, size - 1, 1, &actual) || actual != -0.5f) __builtin_trap();
        if (uwrosv2_boston_dynamics_read_x(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_boston_dynamics_read_y(data, size, 1, &actual) || actual != 1.25f) __builtin_trap();
        if (uwrosv2_boston_dynamics_read_y(data, size - 1, 1, &actual) || actual != 1.25f) __builtin_trap();
        if (uwrosv2_boston_dynamics_read_y(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_boston_dynamics_read_z(data, size, 1, &actual) || actual != 0.75f) __builtin_trap();
        if (uwrosv2_boston_dynamics_read_z(data, size - 1, 1, &actual) || actual != 0.75f) __builtin_trap();
        if (uwrosv2_boston_dynamics_read_z(data, size, SIZE_MAX, &actual)) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
