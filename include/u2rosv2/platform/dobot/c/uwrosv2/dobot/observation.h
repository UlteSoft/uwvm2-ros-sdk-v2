/** Read-only projections of dobot_msgs_v4/RobotStatus. */
#ifndef UWROSV2_DOBOT_OBSERVATION_H
#define UWROSV2_DOBOT_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_dobot_observation_layout[] = {
    {1, 1, 1}, /* is_enable */
    {1, 1, 1}, /* is_connected */
};

/** Read is_enable. Commit the output on success. */
static inline int uwrosv2_dobot_read_is_enable(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_dobot_observation_layout,
                            sizeof uwrosv2_dobot_observation_layout / sizeof uwrosv2_dobot_observation_layout[0], 0, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

/** Read is_connected. Commit the output on success. */
static inline int uwrosv2_dobot_read_is_connected(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_dobot_observation_layout,
                            sizeof uwrosv2_dobot_observation_layout / sizeof uwrosv2_dobot_observation_layout[0], 1, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

#endif
