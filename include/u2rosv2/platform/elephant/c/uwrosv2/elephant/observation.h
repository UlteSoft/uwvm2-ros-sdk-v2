/** Read-only projections of myarm_communication/MyArmPumpStatus. */
#ifndef UWROSV2_ELEPHANT_OBSERVATION_H
#define UWROSV2_ELEPHANT_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_elephant_observation_layout[] = {
    {1, 1, 1}, /* status */
    {1, 1, 0}, /* pin1 */
    {1, 1, 0}, /* pin2 */
};

/** Read status. Commit the output on success. */
static inline int uwrosv2_elephant_read_status(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_elephant_observation_layout,
                            sizeof uwrosv2_elephant_observation_layout / sizeof uwrosv2_elephant_observation_layout[0], 0, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

/** Read pin1. Commit the output on success. */
static inline int uwrosv2_elephant_read_pin1(const uint8_t *data, size_t size, int8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_elephant_observation_layout,
                            sizeof uwrosv2_elephant_observation_layout / sizeof uwrosv2_elephant_observation_layout[0], 1, 0, &bits)) return 0;
    const uint8_t word = (uint8_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read pin2. Commit the output on success. */
static inline int uwrosv2_elephant_read_pin2(const uint8_t *data, size_t size, int8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_elephant_observation_layout,
                            sizeof uwrosv2_elephant_observation_layout / sizeof uwrosv2_elephant_observation_layout[0], 2, 0, &bits)) return 0;
    const uint8_t word = (uint8_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
