/** Read-only projections of geometry_msgs/Quaternion. */
#ifndef UWROSV2_ROS_OBSERVATION_HPP
#define UWROSV2_ROS_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace ros {

static const uwrosv2_obs_field observation_layout[] = {
    {8, 1, 0}, /* x */
    {8, 1, 0}, /* y */
    {8, 1, 0}, /* z */
    {8, 1, 0}, /* w */
};

/** Read x. Commit the output on success. */
static inline bool read_x(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 3, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read y. Commit the output on success. */
static inline bool read_y(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 3, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read z. Commit the output on success. */
static inline bool read_z(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 3, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read w. Commit the output on success. */
static inline bool read_w(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 3, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 3, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::ros

#endif
