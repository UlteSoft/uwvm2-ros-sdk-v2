#include <uwrosv2/abb/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x00, 0x48, 0x41, 0x00, 0x00, 0x30, 0xc0, 0x00, 0x00, 0x00, 0x3f
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        float actual = 0;
        if (!uwrosv2_abb_read_x(data, size, &actual) || actual != 12.5f) __builtin_trap();
        if (uwrosv2_abb_read_x(data, size - 1, &actual) || actual != 12.5f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_abb_read_y(data, size, &actual) || actual != -2.75f) __builtin_trap();
        if (uwrosv2_abb_read_y(data, size - 1, &actual) || actual != -2.75f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_abb_read_z(data, size, &actual) || actual != 0.5f) __builtin_trap();
        if (uwrosv2_abb_read_z(data, size - 1, &actual) || actual != 0.5f) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
