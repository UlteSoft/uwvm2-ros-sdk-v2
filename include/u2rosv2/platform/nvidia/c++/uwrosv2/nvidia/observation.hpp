/** Read-only projections of isaac_ros_nova_interfaces/EncoderTicks. */
#ifndef UWROSV2_NVIDIA_OBSERVATION_HPP
#define UWROSV2_NVIDIA_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace nvidia {

static const uwrosv2_obs_field observation_layout[] = {
    {4, 1, 0}, /* header_stamp_sec */
    {4, 1, 0}, /* header_stamp_nanosec */
    {0, 1, 0}, /* header_frame_id */
    {4, 1, 0}, /* left_ticks */
    {4, 1, 0}, /* right_ticks */
    {8, 1, 0}, /* encoder_timestamp */
};

/** Read left_ticks. Commit the output on success. */
static inline bool read_left_ticks(const uint8_t *data, size_t size, uint32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 3, 0, &bits)) return 0;
    out = (uint32_t)bits;
    return 1;
}

/** Read right_ticks. Commit the output on success. */
static inline bool read_right_ticks(const uint8_t *data, size_t size, uint32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 4, 0, &bits)) return 0;
    out = (uint32_t)bits;
    return 1;
}

/** Read encoder_timestamp. Commit the output on success. */
static inline bool read_encoder_timestamp(const uint8_t *data, size_t size, uint64_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 5, 0, &bits)) return 0;
    out = (uint64_t)bits;
    return 1;
}

} } // namespace uwrosv2::nvidia

#endif
