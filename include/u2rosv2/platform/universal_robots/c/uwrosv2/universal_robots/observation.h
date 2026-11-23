/** Read-only projections of ur_dashboard_msgs/SafetyStatus. */
#ifndef UWROSV2_UNIVERSAL_ROBOTS_OBSERVATION_H
#define UWROSV2_UNIVERSAL_ROBOTS_OBSERVATION_H
#include "../../../../shared/reader.h"

enum { UWROSV2_UNIVERSAL_ROBOTS_NORMAL = 1 };
enum { UWROSV2_UNIVERSAL_ROBOTS_REDUCED = 2 };
enum { UWROSV2_UNIVERSAL_ROBOTS_PROTECTIVE_STOP = 3 };
enum { UWROSV2_UNIVERSAL_ROBOTS_RECOVERY = 4 };
enum { UWROSV2_UNIVERSAL_ROBOTS_SAFEGUARD_STOP = 5 };
enum { UWROSV2_UNIVERSAL_ROBOTS_SYSTEM_EMERGENCY_STOP = 6 };
enum { UWROSV2_UNIVERSAL_ROBOTS_ROBOT_EMERGENCY_STOP = 7 };
enum { UWROSV2_UNIVERSAL_ROBOTS_VIOLATION = 8 };
enum { UWROSV2_UNIVERSAL_ROBOTS_FAULT = 9 };
enum { UWROSV2_UNIVERSAL_ROBOTS_VALIDATE_JOINT_ID = 10 };
enum { UWROSV2_UNIVERSAL_ROBOTS_UNDEFINED_SAFETY_MODE = 11 };
enum { UWROSV2_UNIVERSAL_ROBOTS_AUTOMATIC_MODE_SAFEGUARD_STOP = 12 };
enum { UWROSV2_UNIVERSAL_ROBOTS_SYSTEM_THREE_POSITION_ENABLING_STOP = 13 };
enum { UWROSV2_UNIVERSAL_ROBOTS_TP_THREE_POSITION_ENABLING_STOP = 14 };
enum { UWROSV2_UNIVERSAL_ROBOTS_IMMI_EMERGENCY_STOP = 15 };
enum { UWROSV2_UNIVERSAL_ROBOTS_IMMI_SAFEGUARD_STOP = 16 };
enum { UWROSV2_UNIVERSAL_ROBOTS_PROFISAFE_WAITING_FOR_PARAMETERS = 17 };
enum { UWROSV2_UNIVERSAL_ROBOTS_PROFISAFE_AUTOMATIC_MODE_SAFEGUARD_STOP = 18 };
enum { UWROSV2_UNIVERSAL_ROBOTS_PROFISAFE_SAFEGUARD_STOP = 19 };
enum { UWROSV2_UNIVERSAL_ROBOTS_PROFISAFE_EMERGENCY_STOP = 20 };
enum { UWROSV2_UNIVERSAL_ROBOTS_SAFETY_API_SAFEGUARD_STOP = 22 };
enum { UWROSV2_UNIVERSAL_ROBOTS_IO_PLANE_STOP = 23 };
static const uwrosv2_obs_field uwrosv2_universal_robots_observation_layout[] = {
    {1, 1, 0}, /* status */
};

/** Read status. Commit the output on success. */
static inline int uwrosv2_universal_robots_read_status(const uint8_t *data, size_t size, int8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_universal_robots_observation_layout,
                            sizeof uwrosv2_universal_robots_observation_layout / sizeof uwrosv2_universal_robots_observation_layout[0], 0, 0, &bits)) return 0;
    const uint8_t word = (uint8_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
