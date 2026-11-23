/** Read-only projections of kortex_driver/ActuatorCyclic_Feedback. */
#ifndef UWROSV2_KINOVA_OBSERVATION_H
#define UWROSV2_KINOVA_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_kinova_observation_layout[] = {
    {4, 1, 0}, /* feedback_id_identifier */
    {4, 1, 0}, /* status_flags */
    {4, 1, 0}, /* jitter_comm */
    {4, 1, 0}, /* position */
    {4, 1, 0}, /* velocity */
    {4, 1, 0}, /* torque */
    {4, 1, 0}, /* current_motor */
    {4, 1, 0}, /* voltage */
    {4, 1, 0}, /* temperature_motor */
    {4, 1, 0}, /* temperature_core */
    {4, 1, 0}, /* fault_bank_a */
    {4, 1, 0}, /* fault_bank_b */
    {4, 1, 0}, /* warning_bank_a */
    {4, 1, 0}, /* warning_bank_b */
};

/** Read feedback_id_identifier. Commit the output on success. */
static inline int uwrosv2_kinova_read_feedback_id_identifier(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_kinova_observation_layout,
                            sizeof uwrosv2_kinova_observation_layout / sizeof uwrosv2_kinova_observation_layout[0], 0, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

/** Read jitter_comm. Commit the output on success. */
static inline int uwrosv2_kinova_read_jitter_comm(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_kinova_observation_layout,
                            sizeof uwrosv2_kinova_observation_layout / sizeof uwrosv2_kinova_observation_layout[0], 2, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

/** Read voltage. Commit the output on success. */
static inline int uwrosv2_kinova_read_voltage(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_kinova_observation_layout,
                            sizeof uwrosv2_kinova_observation_layout / sizeof uwrosv2_kinova_observation_layout[0], 7, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read temperature_motor. Commit the output on success. */
static inline int uwrosv2_kinova_read_temperature_motor(const uint8_t *data, size_t size, float *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_kinova_observation_layout,
                            sizeof uwrosv2_kinova_observation_layout / sizeof uwrosv2_kinova_observation_layout[0], 8, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

#endif
