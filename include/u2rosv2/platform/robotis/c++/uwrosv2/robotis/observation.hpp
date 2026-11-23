/** Read-only projections of turtlebot3_msgs/SensorState. */
#ifndef UWROSV2_ROBOTIS_OBSERVATION_HPP
#define UWROSV2_ROBOTIS_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace robotis {

enum { bumper_forward = 1 };
enum { bumper_backward = 2 };
enum { cliff = 1 };
enum { sonar = 1 };
enum { illumination = 1 };
enum { button0 = 1 };
enum { button1 = 2 };
enum { error_left_motor = 1 };
enum { error_right_motor = 2 };
enum { torque_on = 1 };
enum { torque_off = 2 };
static const uwrosv2_obs_field observation_layout[] = {
    {4, 1, 0}, /* header_seq */
    {4, 1, 0}, /* header_stamp_sec */
    {4, 1, 0}, /* header_stamp_nsec */
    {0, 1, 0}, /* header_frame_id */
    {1, 1, 0}, /* bumper */
    {4, 1, 0}, /* cliff */
    {4, 1, 0}, /* sonar */
    {4, 1, 0}, /* illumination */
    {1, 1, 0}, /* led */
    {1, 1, 0}, /* button */
    {1, 1, 1}, /* torque */
    {4, 1, 0}, /* left_encoder */
    {4, 1, 0}, /* right_encoder */
    {4, 1, 0}, /* battery */
};

/** Read bumper. Commit the output on success. */
static inline bool read_bumper(const uint8_t *data, size_t size, uint8_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 4, 0, &bits)) return 0;
    out = (uint8_t)bits;
    return 1;
}

/** Read left_encoder. Commit the output on success. */
static inline bool read_left_encoder(const uint8_t *data, size_t size, int32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 11, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read right_encoder. Commit the output on success. */
static inline bool read_right_encoder(const uint8_t *data, size_t size, int32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 12, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read battery. Commit the output on success. */
static inline bool read_battery(const uint8_t *data, size_t size, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 13, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::robotis

#endif
