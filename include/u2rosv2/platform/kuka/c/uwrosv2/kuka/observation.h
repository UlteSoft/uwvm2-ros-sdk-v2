/** Read-only projections of kuka_driver_interfaces/KssStatus. */
#ifndef UWROSV2_KUKA_OBSERVATION_H
#define UWROSV2_KUKA_OBSERVATION_H
#include "../../../../shared/reader.h"

enum { UWROSV2_KUKA_UNSPECIFIED = 0 };
enum { UWROSV2_KUKA_JOINT_POSITION_CONTROL = 1 };
enum { UWROSV2_KUKA_CARTESIAN_POSITION_CONTROL = 5 };
enum { UWROSV2_KUKA_RSI_4MS = 1 };
enum { UWROSV2_KUKA_RSI_12MS = 2 };
enum { UWROSV2_KUKA_T1 = 1 };
enum { UWROSV2_KUKA_T2 = 2 };
enum { UWROSV2_KUKA_AUT = 3 };
enum { UWROSV2_KUKA_EXT = 4 };
static const uwrosv2_obs_field uwrosv2_kuka_observation_layout[] = {
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
static inline int uwrosv2_kuka_read_cycle_time(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_kuka_observation_layout,
                            sizeof uwrosv2_kuka_observation_layout / sizeof uwrosv2_kuka_observation_layout[0], 1, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

/** Read drives_powered. Commit the output on success. */
static inline int uwrosv2_kuka_read_drives_powered(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_kuka_observation_layout,
                            sizeof uwrosv2_kuka_observation_layout / sizeof uwrosv2_kuka_observation_layout[0], 2, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

/** Read guard_stop. Commit the output on success. */
static inline int uwrosv2_kuka_read_guard_stop(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_kuka_observation_layout,
                            sizeof uwrosv2_kuka_observation_layout / sizeof uwrosv2_kuka_observation_layout[0], 4, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

/** Read operation_mode. Commit the output on success. */
static inline int uwrosv2_kuka_read_operation_mode(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_kuka_observation_layout,
                            sizeof uwrosv2_kuka_observation_layout / sizeof uwrosv2_kuka_observation_layout[0], 7, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

#endif
