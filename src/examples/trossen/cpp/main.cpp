#include <uwrosv2/trossen/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x02, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x6a, 0x6f, 0x69, 0x6e,
    0x74, 0x30, 0x06, 0x00, 0x00, 0x00, 0x6a, 0x6f, 0x69, 0x6e, 0x74, 0x31,
    0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x29, 0x00, 0x00, 0x00
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        int32_t actual = 0;
        if (!uwrosv2::trossen::read_temps(data, size, 1, actual) || actual != 41) __builtin_trap();
        if (uwrosv2::trossen::read_temps(data, size - 1, 1, actual) || actual != 41) __builtin_trap();
        if (uwrosv2::trossen::read_temps(data, size, SIZE_MAX, actual)) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
