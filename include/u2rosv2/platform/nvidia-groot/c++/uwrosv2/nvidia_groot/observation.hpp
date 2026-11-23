/** Read-only projections of DROID observation.state. */
#ifndef UWROSV2_NVIDIA_GROOT_OBSERVATION_HPP
#define UWROSV2_NVIDIA_GROOT_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace nvidia_groot {

static const uwrosv2_obs_field observation_layout[] = {
    {4, 9, 0}, /* eef_9d */
    {4, 1, 0}, /* gripper_position */
    {4, 7, 0}, /* joint_position */
};

/** Read eef_9d at a zero-based index. Commit the output on success. */
static inline bool read_eef_9d(const uint8_t *data, size_t size, size_t index, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, index, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read gripper_position. Commit the output on success. */
static inline bool read_gripper_position(const uint8_t *data, size_t size, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read joint_position at a zero-based index. Commit the output on success. */
static inline bool read_joint_position(const uint8_t *data, size_t size, size_t index, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, index, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::nvidia_groot

#endif
