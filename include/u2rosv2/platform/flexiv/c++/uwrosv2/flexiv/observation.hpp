/** Read-only projections of flexiv_msgs/Digital. */
#ifndef UWROSV2_FLEXIV_OBSERVATION_HPP
#define UWROSV2_FLEXIV_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace flexiv {

static const uwrosv2_obs_field observation_layout[] = {
    {1, 1, 0}, /* pin */
    {1, 1, 1}, /* state */
};

/** Read pin. Commit the output on success. */
static inline bool read_pin(const uint8_t *data, size_t size, uint8_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    out = (uint8_t)bits;
    return 1;
}

/** Read state. Commit the output on success. */
static inline bool read_state(const uint8_t *data, size_t size, bool &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 1, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, 0, &bits)) return 0;
    out = bits != 0;
    return 1;
}

} } // namespace uwrosv2::flexiv

#endif
