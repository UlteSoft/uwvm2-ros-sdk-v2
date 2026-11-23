#include <uwrosv2/ufactory/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa0, 0x3f,
    0x00, 0x00, 0x60, 0x40
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        int32_t actual = 0;
        if (!uwrosv2_ufactory_read_digital_1(data, size, &actual) || actual != 1) __builtin_trap();
        if (uwrosv2_ufactory_read_digital_1(data, size - 1, &actual) || actual != 1) __builtin_trap();
    }
    {
        int32_t actual = 0;
        if (!uwrosv2_ufactory_read_digital_2(data, size, &actual) || actual != 0) __builtin_trap();
        if (uwrosv2_ufactory_read_digital_2(data, size - 1, &actual) || actual != 0) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_ufactory_read_analog_1(data, size, &actual) || actual != 1.25f) __builtin_trap();
        if (uwrosv2_ufactory_read_analog_1(data, size - 1, &actual) || actual != 1.25f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_ufactory_read_analog_2(data, size, &actual) || actual != 3.5f) __builtin_trap();
        if (uwrosv2_ufactory_read_analog_2(data, size - 1, &actual) || actual != 3.5f) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
