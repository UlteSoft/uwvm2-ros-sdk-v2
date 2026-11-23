/** Read-only projections of rm_ros_interfaces/Jointerrorcode. */
#ifndef UWROSV2_REALMAN_OBSERVATION_H
#define UWROSV2_REALMAN_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_realman_observation_layout[] = {
    {2, 0, 0}, /* joint_error */
    {1, 1, 0}, /* dof */
};

/** Read joint_error at a zero-based index. Commit the output on success. */
static inline int uwrosv2_realman_read_joint_error(const uint8_t *data, size_t size, size_t index, uint16_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_realman_observation_layout,
                            sizeof uwrosv2_realman_observation_layout / sizeof uwrosv2_realman_observation_layout[0], 0, index, &bits)) return 0;
    *out = (uint16_t)bits;
    return 1;
}

/** Read dof. Commit the output on success. */
static inline int uwrosv2_realman_read_dof(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_realman_observation_layout,
                            sizeof uwrosv2_realman_observation_layout / sizeof uwrosv2_realman_observation_layout[0], 1, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

#endif
