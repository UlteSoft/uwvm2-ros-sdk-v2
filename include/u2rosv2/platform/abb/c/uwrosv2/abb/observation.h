/** Read-only projections of abb_rapid_msgs/Pos. */
#ifndef UWROSV2_ABB_OBSERVATION_H
#define UWROSV2_ABB_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_abb_observation_layout[] = {
    {4, 1, 0}, /* x */
    {4, 1, 0}, /* y */
    {4, 1, 0}, /* z */
};

/** Read x. Commit the output on success. */
static inline int uwrosv2_abb_read_x(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_abb_observation_layout,
                            sizeof uwrosv2_abb_observation_layout / sizeof uwrosv2_abb_observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read y. Commit the output on success. */
static inline int uwrosv2_abb_read_y(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_abb_observation_layout,
                            sizeof uwrosv2_abb_observation_layout / sizeof uwrosv2_abb_observation_layout[0], 1, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read z. Commit the output on success. */
static inline int uwrosv2_abb_read_z(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_abb_observation_layout,
                            sizeof uwrosv2_abb_observation_layout / sizeof uwrosv2_abb_observation_layout[0], 2, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
