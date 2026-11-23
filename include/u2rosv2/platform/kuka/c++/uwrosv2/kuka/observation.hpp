/** Read-only projections of kuka_driver_interfaces/KssStatus. */
#ifndef UWROSV2_KUKA_OBSERVATION_HPP
#define UWROSV2_KUKA_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace kuka {

enum { unspecified = 0 };
enum { joint_position_control = 1 };
enum { cartesian_position_control = 5 };
enum { rsi_4ms = 1 };
enum { rsi_12ms = 2 };
enum { t1 = 1 };
enum { t2 = 2 };
enum { aut = 3 };
enum { ext = 4 };
static const uwrosv2_obs_field observation_layout[] = {
    {1, 1, 0}, /* control_mode */
    {1, 1, 0}, /* cycle_time */
    {1, 1, 1}, /* drives_powered */
    {1, 1, 1}, /* emergency_stop */
    {1, 1, 1}, /* guard_stop */
    {1, 1, 1}, /* in_motion */
    {1, 1, 1}, /* motion_possible */
    {1, 1, 0}, /* operation_mode */
    {1, 1, 1}, /* robot_stopped */
};

/** Read cycle_time. Commit the output on success. */
static inline bool read_cycle_time(const uint8_t *data, size_t size, uint8_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, 0, &bits)) return 0;
    out = (uint8_t)bits;
    return 1;
}

/** Read drives_powered. Commit the output on success. */
static inline bool read_drives_powered(const uint8_t *data, size_t size, bool &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, 0, &bits)) return 0;
    out = bits != 0;
    return 1;
}

/** Read guard_stop. Commit the output on success. */
static inline bool read_guard_stop(const uint8_t *data, size_t size, bool &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 4, 0, &bits)) return 0;
    out = bits != 0;
    return 1;
}

/** Read operation_mode. Commit the output on success. */
static inline bool read_operation_mode(const uint8_t *data, size_t size, uint8_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 7, 0, &bits)) return 0;
    out = (uint8_t)bits;
    return 1;
}

} } // namespace uwrosv2::kuka

#endif
