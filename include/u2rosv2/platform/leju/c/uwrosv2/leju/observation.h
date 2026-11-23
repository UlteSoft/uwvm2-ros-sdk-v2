/** Read-only projections of kuavo_msgs/BatteryInfo. */
#ifndef UWROSV2_LEJU_OBSERVATION_H
#define UWROSV2_LEJU_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_leju_observation_layout[] = {
    {1, 1, 0}, /* battery_id */
    {4, 1, 0}, /* voltage */
    {4, 1, 0}, /* current */
    {4, 1, 0}, /* remaining_capacity */
    {4, 1, 0}, /* full_capacity */
    {1, 1, 0}, /* percentage */
    {2, 1, 0}, /* cycle_count */
    {4, 1, 0}, /* protection_flags */
    {2, 6, 0}, /* temperatures */
    {4, 1, 0}, /* timestamp_sec */
    {4, 1, 0}, /* timestamp_nsec */
};

/** Read voltage. Commit the output on success. */
static inline int uwrosv2_leju_read_voltage(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_leju_observation_layout,
                            sizeof uwrosv2_leju_observation_layout / sizeof uwrosv2_leju_observation_layout[0], 1, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

/** Read current. Commit the output on success. */
static inline int uwrosv2_leju_read_current(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_leju_observation_layout,
                            sizeof uwrosv2_leju_observation_layout / sizeof uwrosv2_leju_observation_layout[0], 2, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read percentage. Commit the output on success. */
static inline int uwrosv2_leju_read_percentage(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_leju_observation_layout,
                            sizeof uwrosv2_leju_observation_layout / sizeof uwrosv2_leju_observation_layout[0], 5, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

/** Read temperatures at a zero-based index. Commit the output on success. */
static inline int uwrosv2_leju_read_temperatures(const uint8_t *data, size_t size, size_t index, int16_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_leju_observation_layout,
                            sizeof uwrosv2_leju_observation_layout / sizeof uwrosv2_leju_observation_layout[0], 8, index, &bits)) return 0;
    const uint16_t word = (uint16_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
