/** Read-only projections of motoros2_interfaces/ErrorInfo. */
#ifndef UWROSV2_YASKAWA_OBSERVATION_H
#define UWROSV2_YASKAWA_OBSERVATION_H
#include "../../../../shared/reader.h"

static const uwrosv2_obs_field uwrosv2_yaskawa_observation_layout[] = {
    {4, 1, 0}, /* number */
    {0, 1, 0}, /* message */
    {4, 1, 0}, /* sub_code */
    {4, 1, 0}, /* datetime_sec */
    {4, 1, 0}, /* datetime_nanosec */
};

/** Read number. Commit the output on success. */
static inline int uwrosv2_yaskawa_read_number(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_yaskawa_observation_layout,
                            sizeof uwrosv2_yaskawa_observation_layout / sizeof uwrosv2_yaskawa_observation_layout[0], 0, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

/** Read sub_code. Commit the output on success. */
static inline int uwrosv2_yaskawa_read_sub_code(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_yaskawa_observation_layout,
                            sizeof uwrosv2_yaskawa_observation_layout / sizeof uwrosv2_yaskawa_observation_layout[0], 2, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read datetime_sec. Commit the output on success. */
static inline int uwrosv2_yaskawa_read_datetime_sec(const uint8_t *data, size_t size, int32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_yaskawa_observation_layout,
                            sizeof uwrosv2_yaskawa_observation_layout / sizeof uwrosv2_yaskawa_observation_layout[0], 3, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(out, &word, sizeof word);
    return 1;
}

/** Read datetime_nanosec. Commit the output on success. */
static inline int uwrosv2_yaskawa_read_datetime_nanosec(const uint8_t *data, size_t size, uint32_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, uwrosv2_yaskawa_observation_layout,
                            sizeof uwrosv2_yaskawa_observation_layout / sizeof uwrosv2_yaskawa_observation_layout[0], 4, 0, &bits)) return 0;
    *out = (uint32_t)bits;
    return 1;
}

#endif
