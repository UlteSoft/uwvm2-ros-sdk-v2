/** Read-only projections of grab_demo_msgs/GraspCandidate. */
#ifndef UWROSV2_UBTECH_OBSERVATION_HPP
#define UWROSV2_UBTECH_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace ubtech {

static const uwrosv2_obs_field observation_layout[] = {
    {4, 1, 0}, /* header_stamp_sec */
    {4, 1, 0}, /* header_stamp_nanosec */
    {0, 1, 0}, /* header_frame_id */
    {4, 1, 0}, /* pose_header_stamp_sec */
    {4, 1, 0}, /* pose_header_stamp_nanosec */
    {0, 1, 0}, /* pose_header_frame_id */
    {8, 1, 0}, /* pose_pose_position_x */
    {8, 1, 0}, /* pose_pose_position_y */
    {8, 1, 0}, /* pose_pose_position_z */
    {8, 1, 0}, /* pose_pose_orientation_x */
    {8, 1, 0}, /* pose_pose_orientation_y */
    {8, 1, 0}, /* pose_pose_orientation_z */
    {8, 1, 0}, /* pose_pose_orientation_w */
    {0, 1, 0}, /* group_name */
    {4, 1, 0}, /* confidence */
    {0, 1, 0}, /* object_class */
};

/** Read confidence. Commit the output on success. */
static inline bool read_confidence(const uint8_t *data, size_t size, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 14, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read pose_pose_position_z. Commit the output on success. */
static inline bool read_pose_pose_position_z(const uint8_t *data, size_t size, double &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 8, 0, &bits)) return 0;
    const uint64_t word = (uint64_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::ubtech

#endif
