/** Read-only projections of builtin_interfaces/Duration. */
#ifndef UWROSV2_ROS2_OBSERVATION_H
#define UWROSV2_ROS2_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_ros2_observation_layout[] = {
    {4, 1, 0}, /* sec */
    {4, 1, 0}, /* nanosec */
};

/** Read sec. Commit the output on success. */
static inline int uwrosv2_ros2_read_sec(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_ros2_observation_layout,
                            sizeof uwrosv2_ros2_observation_layout / sizeof uwrosv2_ros2_observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read nanosec. Commit the output on success. */
static inline int uwrosv2_ros2_read_nanosec(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_ros2_observation_layout,
                            sizeof uwrosv2_ros2_observation_layout / sizeof uwrosv2_ros2_observation_layout[0], 1, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

#endif
