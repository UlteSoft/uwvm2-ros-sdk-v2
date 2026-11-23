/** Read-only projections of xarm_msgs/IOState. */
#ifndef UWROSV2_UFACTORY_OBSERVATION_H
#define UWROSV2_UFACTORY_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_ufactory_observation_layout[] = {
    {4, 1, 0}, /* digital_1 */
    {4, 1, 0}, /* digital_2 */
    {4, 1, 0}, /* analog_1 */
    {4, 1, 0}, /* analog_2 */
};

/** Read digital_1. Commit the output on success. */
static inline int uwrosv2_ufactory_read_digital_1(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_ufactory_observation_layout,
                            sizeof uwrosv2_ufactory_observation_layout / sizeof uwrosv2_ufactory_observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read digital_2. Commit the output on success. */
static inline int uwrosv2_ufactory_read_digital_2(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_ufactory_observation_layout,
                            sizeof uwrosv2_ufactory_observation_layout / sizeof uwrosv2_ufactory_observation_layout[0], 1, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read analog_1. Commit the output on success. */
static inline int uwrosv2_ufactory_read_analog_1(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_ufactory_observation_layout,
                            sizeof uwrosv2_ufactory_observation_layout / sizeof uwrosv2_ufactory_observation_layout[0], 2, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read analog_2. Commit the output on success. */
static inline int uwrosv2_ufactory_read_analog_2(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_ufactory_observation_layout,
                            sizeof uwrosv2_ufactory_observation_layout / sizeof uwrosv2_ufactory_observation_layout[0], 3, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
