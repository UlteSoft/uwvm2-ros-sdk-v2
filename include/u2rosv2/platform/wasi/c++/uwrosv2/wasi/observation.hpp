/** Read-only projections of __wasi_fdstat_t. */
#ifndef UWROSV2_WASI_OBSERVATION_HPP
#define UWROSV2_WASI_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace wasi {

static const uwrosv2_obs_field observation_layout[] = {
    {1, 1, 0}, /* fs_filetype */
    {1, 1, 0}, /* pad1 */
    {2, 1, 0}, /* fs_flags */
    {1, 4, 0}, /* pad2 */
    {8, 1, 0}, /* fs_rights_base */
    {8, 1, 0}, /* fs_rights_inheriting */
};

/** Read fs_filetype. Commit the output on success. */
static inline bool read_fs_filetype(const uint8_t *data, size_t size, uint8_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    out = (uint8_t)bits;
    return 1;
}

/** Read fs_flags. Commit the output on success. */
static inline bool read_fs_flags(const uint8_t *data, size_t size, uint16_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 2, 0, &bits)) return 0;
    out = (uint16_t)bits;
    return 1;
}

/** Read fs_rights_base. Commit the output on success. */
static inline bool read_fs_rights_base(const uint8_t *data, size_t size, uint64_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 4, 0, &bits)) return 0;
    out = (uint64_t)bits;
    return 1;
}

/** Read fs_rights_inheriting. Commit the output on success. */
static inline bool read_fs_rights_inheriting(const uint8_t *data, size_t size, uint64_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 5, 0, &bits)) return 0;
    out = (uint64_t)bits;
    return 1;
}

} } // namespace uwrosv2::wasi

#endif
