/** Read-only projections of dsr_msgs/LogAlarm. */
#ifndef UWROSV2_DOOSAN_OBSERVATION_H
#define UWROSV2_DOOSAN_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_doosan_observation_layout[] = {
    {4, 1, 0}, /* level */
    {4, 1, 0}, /* group */
    {4, 1, 0}, /* index */
    {0, 3, 0}, /* param */
};

/** Read level. Commit the output on success. */
static inline int uwrosv2_doosan_read_level(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_doosan_observation_layout,
                            sizeof uwrosv2_doosan_observation_layout / sizeof uwrosv2_doosan_observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read group. Commit the output on success. */
static inline int uwrosv2_doosan_read_group(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_doosan_observation_layout,
                            sizeof uwrosv2_doosan_observation_layout / sizeof uwrosv2_doosan_observation_layout[0], 1, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read index. Commit the output on success. */
static inline int uwrosv2_doosan_read_index(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_doosan_observation_layout,
                            sizeof uwrosv2_doosan_observation_layout / sizeof uwrosv2_doosan_observation_layout[0], 2, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
