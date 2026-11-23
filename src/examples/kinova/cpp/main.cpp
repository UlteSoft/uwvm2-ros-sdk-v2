#include <uwrosv2/kinova/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0xd2, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x96, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3e, 0x42, 0x00, 0x00, 0x29, 0x42,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint32_t actual = 0;
        if (!uwrosv2::kinova::read_feedback_id_identifier(data, size, actual) || actual != 1234) __builtin_trap();
        if (uwrosv2::kinova::read_feedback_id_identifier(data, size - 1, actual) || actual != 1234) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2::kinova::read_jitter_comm(data, size, actual) || actual != 150) __builtin_trap();
        if (uwrosv2::kinova::read_jitter_comm(data, size - 1, actual) || actual != 150) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2::kinova::read_voltage(data, size, actual) || actual != 47.5f) __builtin_trap();
        if (uwrosv2::kinova::read_voltage(data, size - 1, actual) || actual != 47.5f) __builtin_trap();
    }
    {
        float actual = 0;
        if (!uwrosv2::kinova::read_temperature_motor(data, size, actual) || actual != 42.25f) __builtin_trap();
        if (uwrosv2::kinova::read_temperature_motor(data, size - 1, actual) || actual != 42.25f) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
