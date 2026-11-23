/** Read-only projections of booster_interface/ImuState. */
#ifndef UWROSV2_BOOSTER_OBSERVATION_HPP
#define UWROSV2_BOOSTER_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace booster {

static const uwrosv2_obs_field observation_layout[] = {
    {4, 3, 0}, /* rpy */
    {4, 3, 0}, /* gyro */
    {4, 3, 0}, /* acc */
};

/** Read rpy at a zero-based index. Commit the output on success. */
static inline bool read_rpy(const uint8_t *data, size_t size, size_t index, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, index, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read gyro at a zero-based index. Commit the output on success. */
static inline bool read_gyro(const uint8_t *data, size_t size, size_t index, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, index, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read acc at a zero-based index. Commit the output on success. */
static inline bool read_acc(const uint8_t *data, size_t size, size_t index, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, index, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::booster

#endif
