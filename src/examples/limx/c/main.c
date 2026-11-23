#include <uwrosv2/limx/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x0c, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x05, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xe4, 0x3f, 0x05, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61,
    0x6d, 0x65
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        double actual = 0;
        if (!uwrosv2_limx_read_estimate_height(data, size, &actual) || actual != 0.625) __builtin_trap();
        if (uwrosv2_limx_read_estimate_height(data, size - 1, &actual) || actual != 0.625) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2_limx_read_header_seq(data, size, &actual) || actual != 524) __builtin_trap();
        if (uwrosv2_limx_read_header_seq(data, size - 1, &actual) || actual != 524) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
}
