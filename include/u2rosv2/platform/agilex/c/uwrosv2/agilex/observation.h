/** Read-only projections of scout_msgs/ScoutBmsStatus. */
#ifndef UWROSV2_AGILEX_OBSERVATION_H
#define UWROSV2_AGILEX_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_agilex_observation_layout[] = {
    {8, 1, 0}, /* soc */
    {8, 1, 0}, /* soh */
    {8, 1, 0}, /* battery_voltage */
    {8, 1, 0}, /* battery_current */
    {8, 1, 0}, /* battery_temperature */
    {1, 1, 0}, /* alarm_status_1 */
    {1, 1, 0}, /* alarm_status_2 */
    {1, 1, 0}, /* warning_status_1 */
    {1, 1, 0}, /* warning_status_2 */
};

/** Read soc. Commit the output on success. */
static inline int uwrosv2_agilex_read_soc(const uint8_t *data, size_t size, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_agilex_observation_layout,
                            sizeof uwrosv2_agilex_observation_layout / sizeof uwrosv2_agilex_observation_layout[0], 0, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read battery_voltage. Commit the output on success. */
static inline int uwrosv2_agilex_read_battery_voltage(const uint8_t *data, size_t size, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_agilex_observation_layout,
                            sizeof uwrosv2_agilex_observation_layout / sizeof uwrosv2_agilex_observation_layout[0], 2, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read battery_current. Commit the output on success. */
static inline int uwrosv2_agilex_read_battery_current(const uint8_t *data, size_t size, double *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_agilex_observation_layout,
                            sizeof uwrosv2_agilex_observation_layout / sizeof uwrosv2_agilex_observation_layout[0], 3, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read alarm_status_1. Commit the output on success. */
static inline int uwrosv2_agilex_read_alarm_status_1(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_agilex_observation_layout,
                            sizeof uwrosv2_agilex_observation_layout / sizeof uwrosv2_agilex_observation_layout[0], 5, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

#endif
