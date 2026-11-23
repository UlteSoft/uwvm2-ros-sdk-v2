/** Read-only projections of simulator_pub_msg. */
#ifndef UWROSV2_FOURIER_OBSERVATION_HPP
#define UWROSV2_FOURIER_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace fourier {

static const uwrosv2_obs_field observation_layout[] = {
    {8, 1, 0}, /* timestamp */
    {4, 1, 2}, /* motor_num */
    {8, -1, 0}, /* q */
    {8, -1, 0}, /* q_dot */
    {8, 3, 0}, /* acc */
    {8, 3, 0}, /* omega */
    {8, 4, 0}, /* quat */
    {8, 1, 0}, /* lf_touch */
    {8, 1, 0}, /* rf_touch */
    {8, 3, 0}, /* pos */
    {8, 3, 0}, /* vel */
};

/** Read timestamp. Commit the output on success. */
static inline bool read_timestamp(const uint8_t *data, size_t size, int64_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 2, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read q at a zero-based index. Commit the output on success. */
static inline bool read_q(const uint8_t *data, size_t size, size_t index, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 2, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, index, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read q_dot at a zero-based index. Commit the output on success. */
static inline bool read_q_dot(const uint8_t *data, size_t size, size_t index, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 2, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 3, index, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read lf_touch. Commit the output on success. */
static inline bool read_lf_touch(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 2, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 7, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read rf_touch. Commit the output on success. */
static inline bool read_rf_touch(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 2, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 8, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::fourier

#endif
