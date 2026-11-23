/** Read-only projections of isaac_ros_nova_interfaces/EncoderTicks. */
#ifndef UWROSV2_NVIDIA_OBSERVATION_H
#define UWROSV2_NVIDIA_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_nvidia_observation_layout[] = {
    {4, 1, 0}, /* header_stamp_sec */
    {4, 1, 0}, /* header_stamp_nanosec */
    {0, 1, 0}, /* header_frame_id */
    {4, 1, 0}, /* left_ticks */
    {4, 1, 0}, /* right_ticks */
    {8, 1, 0}, /* encoder_timestamp */
};

/** Read left_ticks. Commit the output on success. */
static inline int uwrosv2_nvidia_read_left_ticks(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_nvidia_observation_layout,
                            sizeof uwrosv2_nvidia_observation_layout / sizeof uwrosv2_nvidia_observation_layout[0], 3, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

/** Read right_ticks. Commit the output on success. */
static inline int uwrosv2_nvidia_read_right_ticks(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_nvidia_observation_layout,
                            sizeof uwrosv2_nvidia_observation_layout / sizeof uwrosv2_nvidia_observation_layout[0], 4, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

/** Read encoder_timestamp. Commit the output on success. */
static inline int uwrosv2_nvidia_read_encoder_timestamp(const uint8_t *data, size_t size, uint64_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_nvidia_observation_layout,
                            sizeof uwrosv2_nvidia_observation_layout / sizeof uwrosv2_nvidia_observation_layout[0], 5, 0, &bits)) return 0;
    *out = (uint64_t)bits;
    return 1;
}

#endif
