/** Read-only projections of aimdk_msgs/JointState. */
#ifndef UWROSV2_AGIBOT_OBSERVATION_HPP
#define UWROSV2_AGIBOT_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace agibot {

static const uwrosv2_obs_field observation_layout[] = {
    {0, 1, 0}, /* name */
    {8, 1, 0}, /* position */
    {8, 1, 0}, /* velocity */
    {8, 1, 0}, /* effort */
    {2, 1, 0}, /* error_code */
};

/** Read position. Commit the output on success. */
static inline bool read_position(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read velocity. Commit the output on success. */
static inline bool read_velocity(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read effort. Commit the output on success. */
static inline bool read_effort(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 3, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read error_code. Commit the output on success. */
static inline bool read_error_code(const uint8_t *data, size_t size, uint16_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 4, 0, &bits)) return 0;
    out = (uint16_t)bits;
    return 1;
}

} } // namespace uwrosv2::agibot

#endif
