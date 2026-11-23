#include <uwrosv2/agilex/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x60, 0x52, 0x40, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x48, 0x40,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf8, 0xbf, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        double actual = 0;
        if (!uwrosv2::agilex::read_soc(data, size, actual) || actual != 73.5) __builtin_trap();
        if (uwrosv2::agilex::read_soc(data, size - 1, actual) || actual != 73.5) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2::agilex::read_battery_voltage(data, size, actual) || actual != 48.25) __builtin_trap();
        if (uwrosv2::agilex::read_battery_voltage(data, size - 1, actual) || actual != 48.25) __builtin_trap();
    }
    {
        double actual = 0;
        if (!uwrosv2::agilex::read_battery_current(data, size, actual) || actual != -1.5) __builtin_trap();
        if (uwrosv2::agilex::read_battery_current(data, size - 1, actual) || actual != -1.5) __builtin_trap();
    }
    {
        uint8_t actual = 0;
        if (!uwrosv2::agilex::read_alarm_status_1(data, size, actual) || actual != 2) __builtin_trap();
        if (uwrosv2::agilex::read_alarm_status_1(data, size - 1, actual) || actual != 2) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
