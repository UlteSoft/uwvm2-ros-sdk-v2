/** Read-only projections of limxsdk::msg::perception_msgs::HeightEstimateResult. */
#ifndef UWROSV2_LIMX_OBSERVATION_HPP
#define UWROSV2_LIMX_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace limx {

static const uwrosv2_obs_field observation_layout[] = {
    {4, 1, 0}, /* header_seq */
    {4, 1, 0}, /* header_stamp_sec */
    {4, 1, 0}, /* header_stamp_nsec */
    {0, 1, 0}, /* header_frame_id */
    {8, 1, 0}, /* estimate_height */
    {0, 1, 0}, /* desc */
};

/** Read estimate_height. Commit the output on success. */
static inline bool read_estimate_height(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 4, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read header_seq. Commit the output on success. */
static inline bool read_header_seq(const uint8_t *data, size_t size, uint32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    out = (uint32_t)bits;
    return 1;
}

} } // namespace uwrosv2::limx

#endif
