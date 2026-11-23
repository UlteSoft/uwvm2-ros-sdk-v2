/** Read-only projections of isaac_ros_tensor_list_interfaces/TensorShape. */
#ifndef UWROSV2_NVIDIA_ISAAC_ROS_OBSERVATION_H
#define UWROSV2_NVIDIA_ISAAC_ROS_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_nvidia_isaac_ros_observation_layout[] = {
    {1, 1, 0}, /* rank */
    {4, 0, 0}, /* dims */
};

/** Read rank. Commit the output on success. */
static inline int uwrosv2_nvidia_isaac_ros_read_rank(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_nvidia_isaac_ros_observation_layout,
                            sizeof uwrosv2_nvidia_isaac_ros_observation_layout / sizeof uwrosv2_nvidia_isaac_ros_observation_layout[0], 0, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

/** Read dims at a zero-based index. Commit the output on success. */
static inline int uwrosv2_nvidia_isaac_ros_read_dims(const uint8_t *data, size_t size, size_t index, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_nvidia_isaac_ros_observation_layout,
                            sizeof uwrosv2_nvidia_isaac_ros_observation_layout / sizeof uwrosv2_nvidia_isaac_ros_observation_layout[0], 1, index, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

#endif
