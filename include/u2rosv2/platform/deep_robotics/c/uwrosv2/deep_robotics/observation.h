/** Read-only projections of drdds/ImuDataValue. */
#ifndef UWROSV2_DEEP_ROBOTICS_OBSERVATION_H
#define UWROSV2_DEEP_ROBOTICS_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_deep_robotics_observation_layout[] = {
    {4, 1, 0}, /* roll */
    {4, 1, 0}, /* pitch */
    {4, 1, 0}, /* yaw */
    {4, 1, 0}, /* omega_x */
    {4, 1, 0}, /* omega_y */
    {4, 1, 0}, /* omega_z */
    {4, 1, 0}, /* acc_x */
    {4, 1, 0}, /* acc_y */
    {4, 1, 0}, /* acc_z */
};

/** Read roll. Commit the output on success. */
static inline int uwrosv2_deep_robotics_read_roll(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_deep_robotics_observation_layout,
                            sizeof uwrosv2_deep_robotics_observation_layout / sizeof uwrosv2_deep_robotics_observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read yaw. Commit the output on success. */
static inline int uwrosv2_deep_robotics_read_yaw(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_deep_robotics_observation_layout,
                            sizeof uwrosv2_deep_robotics_observation_layout / sizeof uwrosv2_deep_robotics_observation_layout[0], 2, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read omega_z. Commit the output on success. */
static inline int uwrosv2_deep_robotics_read_omega_z(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_deep_robotics_observation_layout,
                            sizeof uwrosv2_deep_robotics_observation_layout / sizeof uwrosv2_deep_robotics_observation_layout[0], 5, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read acc_z. Commit the output on success. */
static inline int uwrosv2_deep_robotics_read_acc_z(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_deep_robotics_observation_layout,
                            sizeof uwrosv2_deep_robotics_observation_layout / sizeof uwrosv2_deep_robotics_observation_layout[0], 8, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
