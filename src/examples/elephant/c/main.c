#include <uwrosv2/elephant/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x01, 0xff, 0x02
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint8_t actual = 0;
        if (!uwrosv2_elephant_read_status(data, size, &actual) || actual != 1) __builtin_trap();
        if (uwrosv2_elephant_read_status(data, size - 1, &actual) || actual != 1) __builtin_trap();
    }
    {
        int8_t actual = 0;
        if (!uwrosv2_elephant_read_pin1(data, size, &actual) || actual != -1) __builtin_trap();
        if (uwrosv2_elephant_read_pin1(data, size - 1, &actual) || actual != -1) __builtin_trap();
    }
    {
        int8_t actual = 0;
        if (!uwrosv2_elephant_read_pin2(data, size, &actual) || actual != 2) __builtin_trap();
        if (uwrosv2_elephant_read_pin2(data, size - 1, &actual) || actual != 2) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
