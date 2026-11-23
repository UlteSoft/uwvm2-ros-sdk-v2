/** Read-only projections of franka_msgs/Elbow. */
#ifndef UWROSV2_FRANKA_OBSERVATION_H
#define UWROSV2_FRANKA_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_franka_observation_layout[] = {
    {8, 2, 0}, /* position */
    {8, 2, 0}, /* desired_position */
    {8, 2, 0}, /* commanded_position */
    {8, 2, 0}, /* commanded_velocity */
    {8, 2, 0}, /* commanded_acceleration */
};

/** Read position at a zero-based index. Commit the output on success. */
static inline int uwrosv2_franka_read_position(const uint8_t *data, size_t size, size_t index, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_franka_observation_layout,
                            sizeof uwrosv2_franka_observation_layout / sizeof uwrosv2_franka_observation_layout[0], 0, index, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read desired_position at a zero-based index. Commit the output on success. */
static inline int uwrosv2_franka_read_desired_position(const uint8_t *data, size_t size, size_t index, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_franka_observation_layout,
                            sizeof uwrosv2_franka_observation_layout / sizeof uwrosv2_franka_observation_layout[0], 1, index, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read commanded_position at a zero-based index. Commit the output on success. */
static inline int uwrosv2_franka_read_commanded_position(const uint8_t *data, size_t size, size_t index, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_franka_observation_layout,
                            sizeof uwrosv2_franka_observation_layout / sizeof uwrosv2_franka_observation_layout[0], 2, index, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read commanded_velocity at a zero-based index. Commit the output on success. */
static inline int uwrosv2_franka_read_commanded_velocity(const uint8_t *data, size_t size, size_t index, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_franka_observation_layout,
                            sizeof uwrosv2_franka_observation_layout / sizeof uwrosv2_franka_observation_layout[0], 3, index, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read commanded_acceleration at a zero-based index. Commit the output on success. */
static inline int uwrosv2_franka_read_commanded_acceleration(const uint8_t *data, size_t size, size_t index, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_franka_observation_layout,
                            sizeof uwrosv2_franka_observation_layout / sizeof uwrosv2_franka_observation_layout[0], 4, index, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
