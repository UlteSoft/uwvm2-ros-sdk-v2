/** Read-only projections of turtlebot3_msgs/SensorState. */
#ifndef UWROSV2_ROBOTIS_OBSERVATION_H
#define UWROSV2_ROBOTIS_OBSERVATION_H
#include "../../../../shared/reader.h"

enum { UWROSV2_ROBOTIS_BUMPER_FORWARD = 1 };
enum { UWROSV2_ROBOTIS_BUMPER_BACKWARD = 2 };
enum { UWROSV2_ROBOTIS_CLIFF = 1 };
enum { UWROSV2_ROBOTIS_SONAR = 1 };
enum { UWROSV2_ROBOTIS_ILLUMINATION = 1 };
enum { UWROSV2_ROBOTIS_BUTTON0 = 1 };
enum { UWROSV2_ROBOTIS_BUTTON1 = 2 };
enum { UWROSV2_ROBOTIS_ERROR_LEFT_MOTOR = 1 };
enum { UWROSV2_ROBOTIS_ERROR_RIGHT_MOTOR = 2 };
enum { UWROSV2_ROBOTIS_TORQUE_ON = 1 };
enum { UWROSV2_ROBOTIS_TORQUE_OFF = 2 };
static const uwrosv2_obs_field uwrosv2_robotis_observation_layout[] = {
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
static inline int uwrosv2_robotis_read_bumper(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_robotis_observation_layout,
                            sizeof uwrosv2_robotis_observation_layout / sizeof uwrosv2_robotis_observation_layout[0], 4, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

/** Read left_encoder. Commit the output on success. */
static inline int uwrosv2_robotis_read_left_encoder(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_robotis_observation_layout,
                            sizeof uwrosv2_robotis_observation_layout / sizeof uwrosv2_robotis_observation_layout[0], 11, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read right_encoder. Commit the output on success. */
static inline int uwrosv2_robotis_read_right_encoder(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_robotis_observation_layout,
                            sizeof uwrosv2_robotis_observation_layout / sizeof uwrosv2_robotis_observation_layout[0], 12, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read battery. Commit the output on success. */
static inline int uwrosv2_robotis_read_battery(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_robotis_observation_layout,
                            sizeof uwrosv2_robotis_observation_layout / sizeof uwrosv2_robotis_observation_layout[0], 13, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
