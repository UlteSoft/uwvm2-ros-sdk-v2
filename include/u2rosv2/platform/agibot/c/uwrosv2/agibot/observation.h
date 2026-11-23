/** Read-only projections of aimdk_msgs/JointState. */
#ifndef UWROSV2_AGIBOT_OBSERVATION_H
#define UWROSV2_AGIBOT_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_agibot_observation_layout[] = {
    {0, 1, 0}, /* name */
    {8, 1, 0}, /* position */
    {8, 1, 0}, /* velocity */
    {8, 1, 0}, /* effort */
    {2, 1, 0}, /* error_code */
};

/** Read position. Commit the output on success. */
static inline int uwrosv2_agibot_read_position(const uint8_t *data, size_t size, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_agibot_observation_layout,
                            sizeof uwrosv2_agibot_observation_layout / sizeof uwrosv2_agibot_observation_layout[0], 1, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read velocity. Commit the output on success. */
static inline int uwrosv2_agibot_read_velocity(const uint8_t *data, size_t size, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_agibot_observation_layout,
                            sizeof uwrosv2_agibot_observation_layout / sizeof uwrosv2_agibot_observation_layout[0], 2, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read effort. Commit the output on success. */
static inline int uwrosv2_agibot_read_effort(const uint8_t *data, size_t size, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_agibot_observation_layout,
                            sizeof uwrosv2_agibot_observation_layout / sizeof uwrosv2_agibot_observation_layout[0], 3, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read error_code. Commit the output on success. */
static inline int uwrosv2_agibot_read_error_code(const uint8_t *data, size_t size, uint16_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_agibot_observation_layout,
                            sizeof uwrosv2_agibot_observation_layout / sizeof uwrosv2_agibot_observation_layout[0], 4, 0, &bits)) return 0;
    *out = (uint16_t)bits;
    return 1;
}

#endif
