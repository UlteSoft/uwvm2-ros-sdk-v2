/** Read-only projections of std_msgs/Time. */
#ifndef UWROSV2_ROS1_OBSERVATION_H
#define UWROSV2_ROS1_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_ros1_observation_layout[] = {
    {4, 1, 0}, /* data_sec */
    {4, 1, 0}, /* data_nsec */
};

/** Read data_sec. Commit the output on success. */
static inline int uwrosv2_ros1_read_data_sec(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_ros1_observation_layout,
                            sizeof uwrosv2_ros1_observation_layout / sizeof uwrosv2_ros1_observation_layout[0], 0, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

/** Read data_nsec. Commit the output on success. */
static inline int uwrosv2_ros1_read_data_nsec(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_ros1_observation_layout,
                            sizeof uwrosv2_ros1_observation_layout / sizeof uwrosv2_ros1_observation_layout[0], 1, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

#endif
