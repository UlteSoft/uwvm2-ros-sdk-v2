/** Read-only projections of Isaac Sim ROS2 Publish Clock / rosgraph_msgs/Clock. */
#ifndef UWROSV2_NVIDIA_ISAAC_SIM_OBSERVATION_H
#define UWROSV2_NVIDIA_ISAAC_SIM_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_nvidia_isaac_sim_observation_layout[] = {
    {4, 1, 0}, /* clock_sec */
    {4, 1, 0}, /* clock_nanosec */
};

/** Read clock_sec. Commit the output on success. */
static inline int uwrosv2_nvidia_isaac_sim_read_clock_sec(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_nvidia_isaac_sim_observation_layout,
                            sizeof uwrosv2_nvidia_isaac_sim_observation_layout / sizeof uwrosv2_nvidia_isaac_sim_observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read clock_nanosec. Commit the output on success. */
static inline int uwrosv2_nvidia_isaac_sim_read_clock_nanosec(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_nvidia_isaac_sim_observation_layout,
                            sizeof uwrosv2_nvidia_isaac_sim_observation_layout / sizeof uwrosv2_nvidia_isaac_sim_observation_layout[0], 1, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

#endif
