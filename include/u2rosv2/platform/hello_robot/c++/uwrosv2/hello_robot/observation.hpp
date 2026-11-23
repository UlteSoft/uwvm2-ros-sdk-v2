/** Read-only projections of Wacc_Protocol_P0.unpack_status. */
#ifndef UWROSV2_HELLO_ROBOT_OBSERVATION_HPP
#define UWROSV2_HELLO_ROBOT_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace hello_robot {

static const uwrosv2_obs_field observation_layout[] = {
    {4, 1, 0}, /* ax */
    {4, 1, 0}, /* ay */
    {4, 1, 0}, /* az */
    {2, 1, 0}, /* a0 */
    {1, 1, 0}, /* d0 */
    {1, 1, 0}, /* d1 */
    {1, 1, 0}, /* d2 */
    {1, 1, 0}, /* d3 */
    {4, 1, 0}, /* single_tap_count */
    {4, 1, 0}, /* state */
    {4, 1, 0}, /* timestamp */
    {4, 1, 0}, /* debug */
};

/** Read ax. Commit the output on success. */
static inline bool read_ax(const uint8_t *data, size_t size, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read az. Commit the output on success. */
static inline bool read_az(const uint8_t *data, size_t size, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read a0. Commit the output on success. */
static inline bool read_a0(const uint8_t *data, size_t size, int16_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 3, 0, &bits)) return 0;
    const uint16_t word = (uint16_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read single_tap_count. Commit the output on success. */
static inline bool read_single_tap_count(const uint8_t *data, size_t size, uint32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 8, 0, &bits)) return 0;
    out = (uint32_t)bits;
    return 1;
}

/** Read timestamp. Commit the output on success. */
static inline bool read_timestamp(const uint8_t *data, size_t size, uint32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 10, 0, &bits)) return 0;
    out = (uint32_t)bits;
    return 1;
}

} } // namespace uwrosv2::hello_robot

#endif
