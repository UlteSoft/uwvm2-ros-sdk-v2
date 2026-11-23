#include <uwrosv2/nvidia_isaac_sim/observation.h>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0xa0, 0xac, 0xb9, 0x03
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05, 0x03, 0xb9, 0xac, 0xa0
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        int32_t actual = 0;
        if (!uwrosv2_nvidia_isaac_sim_read_clock_sec(data, size, &actual) || actual != 5) __builtin_trap();
        if (uwrosv2_nvidia_isaac_sim_read_clock_sec(data, size - 1, &actual) || actual != 5) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2_nvidia_isaac_sim_read_clock_nanosec(data, size, &actual) || actual != 62500000) __builtin_trap();
        if (uwrosv2_nvidia_isaac_sim_read_clock_nanosec(data, size - 1, &actual) || actual != 62500000) __builtin_trap();
    }
}

void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
