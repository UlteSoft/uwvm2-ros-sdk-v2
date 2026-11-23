/** Read-only projections of fanuc_msgs/ForceSensor. */
#ifndef UWROSV2_FANUC_OBSERVATION_HPP
#define UWROSV2_FANUC_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace fanuc {

static const uwrosv2_obs_field observation_layout[] = {
    {4, 1, 0}, /* force_x */
    {4, 1, 0}, /* force_y */
    {4, 1, 0}, /* force_z */
    {4, 1, 0}, /* moment_x */
    {4, 1, 0}, /* moment_y */
    {4, 1, 0}, /* moment_z */
    {4, 1, 0}, /* fs_type */
};

/** Read force_x. Commit the output on success. */
static inline bool read_force_x(const uint8_t *data, size_t size, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read force_z. Commit the output on success. */
static inline bool read_force_z(const uint8_t *data, size_t size, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read moment_z. Commit the output on success. */
static inline bool read_moment_z(const uint8_t *data, size_t size, float &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 5, 0, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

/** Read fs_type. Commit the output on success. */
static inline bool read_fs_type(const uint8_t *data, size_t size, uint32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 6, 0, &bits)) return 0;
    out = (uint32_t)bits;
    return 1;
}

} } // namespace uwrosv2::fanuc

#endif
