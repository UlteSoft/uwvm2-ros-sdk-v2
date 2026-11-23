/** Read-only projections of dobot_msgs_v4/RobotStatus. */
#ifndef UWROSV2_DOBOT_OBSERVATION_HPP
#define UWROSV2_DOBOT_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace dobot {

static const uwrosv2_obs_field observation_layout[] = {
    {1, 1, 1}, /* is_enable */
    {1, 1, 1}, /* is_connected */
};

/** Read is_enable. Commit the output on success. */
static inline bool read_is_enable(const uint8_t *data, size_t size, bool &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    out = bits != 0;
    return 1;
}

/** Read is_connected. Commit the output on success. */
static inline bool read_is_connected(const uint8_t *data, size_t size, bool &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, 0, &bits)) return 0;
    out = bits != 0;
    return 1;
}

} } // namespace uwrosv2::dobot

#endif
