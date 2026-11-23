/** Read-only projections of pal_device_msgs/BatteryState. */
#ifndef UWROSV2_PAL_OBSERVATION_H
#define UWROSV2_PAL_OBSERVATION_H
#include "../../../../shared/reader.h"

enum { UWROSV2_PAL_FULL = 5 };
enum { UWROSV2_PAL_HIGH = 4 };
enum { UWROSV2_PAL_MEDIUM = 3 };
enum { UWROSV2_PAL_LOW = 2 };
enum { UWROSV2_PAL_CRITICAL_LOW = 1 };
static const uwrosv2_obs_field uwrosv2_pal_observation_layout[] = {
    {1, 1, 0}, /* charge_state */
    {4, 1, 0}, /* battery_percentage */
};

/** Read charge_state. Commit the output on success. */
static inline int uwrosv2_pal_read_charge_state(const uint8_t *data, size_t size, int8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_pal_observation_layout,
                            sizeof uwrosv2_pal_observation_layout / sizeof uwrosv2_pal_observation_layout[0], 0, 0, &bits)) return 0;
    const uint8_t word = (uint8_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read battery_percentage. Commit the output on success. */
static inline int uwrosv2_pal_read_battery_percentage(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_pal_observation_layout,
                            sizeof uwrosv2_pal_observation_layout / sizeof uwrosv2_pal_observation_layout[0], 1, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
