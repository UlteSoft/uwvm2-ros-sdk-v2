/** Read-only projections of dsr_msgs/LogAlarm. */
#ifndef UWROSV2_DOOSAN_OBSERVATION_HPP
#define UWROSV2_DOOSAN_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace doosan {

static const uwrosv2_obs_field observation_layout[] = {
    {4, 1, 0}, /* level */
    {4, 1, 0}, /* group */
    {4, 1, 0}, /* index */
    {0, 3, 0}, /* param */
};

/** Read level. Commit the output on success. */
static inline bool read_level(const uint8_t *data, size_t size, int32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read group. Commit the output on success. */
static inline bool read_group(const uint8_t *data, size_t size, int32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read index. Commit the output on success. */
static inline bool read_index(const uint8_t *data, size_t size, int32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::doosan

#endif
