/** Read-only projections of booster_interface/ImuState. */
#ifndef UWROSV2_BOOSTER_OBSERVATION_H
#define UWROSV2_BOOSTER_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_booster_observation_layout[] = {
    {4, 3, 0}, /* rpy */
    {4, 3, 0}, /* gyro */
    {4, 3, 0}, /* acc */
};

/** Read rpy at a zero-based index. Commit the output on success. */
static inline int uwrosv2_booster_read_rpy(const uint8_t *data, size_t size, size_t index, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_booster_observation_layout,
                            sizeof uwrosv2_booster_observation_layout / sizeof uwrosv2_booster_observation_layout[0], 0, index, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read gyro at a zero-based index. Commit the output on success. */
static inline int uwrosv2_booster_read_gyro(const uint8_t *data, size_t size, size_t index, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_booster_observation_layout,
                            sizeof uwrosv2_booster_observation_layout / sizeof uwrosv2_booster_observation_layout[0], 1, index, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read acc at a zero-based index. Commit the output on success. */
static inline int uwrosv2_booster_read_acc(const uint8_t *data, size_t size, size_t index, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_booster_observation_layout,
                            sizeof uwrosv2_booster_observation_layout / sizeof uwrosv2_booster_observation_layout[0], 2, index, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
