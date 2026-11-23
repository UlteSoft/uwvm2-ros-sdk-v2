/** Read-only projections of builtin_interfaces/Duration. */
#ifndef UWROSV2_ROS2_OBSERVATION_HPP
#define UWROSV2_ROS2_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace ros2 {

static const uwrosv2_obs_field observation_layout[] = {
    {4, 1, 0}, /* sec */
    {4, 1, 0}, /* nanosec */
};

/** Read sec. Commit the output on success. */
static inline bool read_sec(const uint8_t *data, size_t size, int32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read nanosec. Commit the output on success. */
static inline bool read_nanosec(const uint8_t *data, size_t size, uint32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, 0, &bits)) return 0;
    out = (uint32_t)bits;
    return 1;
}

} } // namespace uwrosv2::ros2

#endif
