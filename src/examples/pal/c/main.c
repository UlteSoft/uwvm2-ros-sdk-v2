#include <uwrosv2/pal/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x03, 0x00, 0x00, 0x87, 0x42
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        int8_t actual = 0;
        if (!uwrosv2_pal_read_charge_state(data, size, &actual) || actual != 3) __builtin_trap();
        if (uwrosv2_pal_read_charge_state(data, size - 1, &actual) || actual != 3) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2_pal_read_battery_percentage(data, size, &actual) || actual != 67.5f) __builtin_trap();
        if (uwrosv2_pal_read_battery_percentage(data, size - 1, &actual) || actual != 67.5f) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
