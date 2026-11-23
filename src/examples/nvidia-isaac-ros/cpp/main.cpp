#include <uwrosv2/nvidia_isaac_ros/observation.hpp>

/* Constructed from the pinned interface definition. */
static const volatile uint8_t example[] = {
    0x00, 0x01, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x80, 0x02, 0x00, 0x00
};

static const volatile uint8_t big_endian[] = {
    0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x80
};

static void check_frame(const volatile uint8_t *source, size_t size) UWROSV2_OBS_NOEXCEPT {
    uint8_t data[sizeof example];
    for (size_t i = 0; i < size; ++i) data[i] = source[i];
    {
        uint8_t actual = 0;
        if (!uwrosv2::nvidia_isaac_ros::read_rank(data, size, actual) || actual != 2) __builtin_trap();
        if (uwrosv2::nvidia_isaac_ros::read_rank(data, size - 1, actual) || actual != 2) __builtin_trap();
    }
    {
        uint32_t actual = 0;
        if (!uwrosv2::nvidia_isaac_ros::read_dims(data, size, 1, actual) || actual != 640) __builtin_trap();
        if (uwrosv2::nvidia_isaac_ros::read_dims(data, size - 1, 1, actual) || actual != 640) __builtin_trap();
        if (uwrosv2::nvidia_isaac_ros::read_dims(data, size, SIZE_MAX, actual)) __builtin_trap();
    }
}

extern "C" void _start(void) UWROSV2_OBS_NOEXCEPT {
    check_frame(example, sizeof example);
    check_frame(big_endian, sizeof big_endian);
}
