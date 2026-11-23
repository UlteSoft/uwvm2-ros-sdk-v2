/** Read-only projections of bosdyn.api.PointCloud.data. */
#ifndef UWROSV2_BOSTON_DYNAMICS_OBSERVATION_H
#define UWROSV2_BOSTON_DYNAMICS_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_boston_dynamics_observation_layout[] = {
    {4, -4, 0}, /* xyz */
};

/** Read xyz at a zero-based index. Commit the output on success. */
static inline int uwrosv2_boston_dynamics_read_x(const uint8_t *data, size_t size, size_t index, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    if (index > (SIZE_MAX - 0u) / 3u) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_boston_dynamics_observation_layout,
                            sizeof uwrosv2_boston_dynamics_observation_layout / sizeof uwrosv2_boston_dynamics_observation_layout[0], 0, index * 3u + 0u, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read xyz at a zero-based index. Commit the output on success. */
static inline int uwrosv2_boston_dynamics_read_y(const uint8_t *data, size_t size, size_t index, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    if (index > (SIZE_MAX - 1u) / 3u) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_boston_dynamics_observation_layout,
                            sizeof uwrosv2_boston_dynamics_observation_layout / sizeof uwrosv2_boston_dynamics_observation_layout[0], 0, index * 3u + 1u, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read xyz at a zero-based index. Commit the output on success. */
static inline int uwrosv2_boston_dynamics_read_z(const uint8_t *data, size_t size, size_t index, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    if (index > (SIZE_MAX - 2u) / 3u) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_boston_dynamics_observation_layout,
                            sizeof uwrosv2_boston_dynamics_observation_layout / sizeof uwrosv2_boston_dynamics_observation_layout[0], 0, index * 3u + 2u, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
