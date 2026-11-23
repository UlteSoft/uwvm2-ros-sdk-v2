/** Read-only projections of ur_dashboard_msgs/SafetyStatus. */
#ifndef UWROSV2_UNIVERSAL_ROBOTS_OBSERVATION_HPP
#define UWROSV2_UNIVERSAL_ROBOTS_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace universal_robots {

enum { normal = 1 };
enum { reduced = 2 };
enum { protective_stop = 3 };
enum { recovery = 4 };
enum { safeguard_stop = 5 };
enum { system_emergency_stop = 6 };
enum { robot_emergency_stop = 7 };
enum { violation = 8 };
enum { fault = 9 };
enum { validate_joint_id = 10 };
enum { undefined_safety_mode = 11 };
enum { automatic_mode_safeguard_stop = 12 };
enum { system_three_position_enabling_stop = 13 };
enum { tp_three_position_enabling_stop = 14 };
enum { immi_emergency_stop = 15 };
enum { immi_safeguard_stop = 16 };
enum { profisafe_waiting_for_parameters = 17 };
enum { profisafe_automatic_mode_safeguard_stop = 18 };
enum { profisafe_safeguard_stop = 19 };
enum { profisafe_emergency_stop = 20 };
enum { safety_api_safeguard_stop = 22 };
enum { io_plane_stop = 23 };
static const uwrosv2_obs_field observation_layout[] = {
    {1, 1, 0}, /* status */
};

/** Read status. Commit the output on success. */
static inline bool read_status(const uint8_t *data, size_t size, int8_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    const uint8_t word = (uint8_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::universal_robots

#endif
