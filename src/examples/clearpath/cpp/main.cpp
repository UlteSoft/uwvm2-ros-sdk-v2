#include <uwrosv2/clearpath/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x03
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint8_t actual = 0;
        if (!uwrosv2::clearpath::read_state(data, size, actual) || actual != 3) __builtin_trap();
        if (uwrosv2::clearpath::read_state(data, size - 1, actual) || actual != 3) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
