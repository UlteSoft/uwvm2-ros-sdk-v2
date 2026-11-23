/** Read-only projections of pal_device_msgs/BatteryState. */
#ifndef UWROSV2_PAL_OBSERVATION_HPP
#define UWROSV2_PAL_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace pal {

enum { full = 5 };
enum { high = 4 };
enum { medium = 3 };
enum { low = 2 };
enum { critical_low = 1 };
static const uwrosv2_obs_field observation_layout[] = {
    {1, 1, 0}, /* charge_state */
    {4, 1, 0}, /* battery_percentage */
};

/** Read charge_state. Commit the output on success. */
static inline bool read_charge_state(const uint8_t *data, size_t size, int8_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    const uint8_t word = (uint8_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read battery_percentage. Commit the output on success. */
static inline bool read_battery_percentage(const uint8_t *data, size_t size, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::pal

#endif
