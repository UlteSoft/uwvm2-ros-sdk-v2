/** Read-only projections of interbotix_xs_msgs/JointTemps. */
#ifndef UWROSV2_TROSSEN_OBSERVATION_HPP
#define UWROSV2_TROSSEN_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace trossen {

static const uwrosv2_obs_field observation_layout[] = {
    {0, 0, 0}, /* names */
    {4, 0, 0}, /* temps */
};

/** Read temps at a zero-based index. Commit the output on success. */
static inline bool read_temps(const uint8_t *data, size_t size, size_t index, int32_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 1, index, &bits)) return 0;
    const uint32_t word = (uint32_t)bits;
    memcpy(&out, &word, sizeof word);
    return 1;
}

} } // namespace uwrosv2::trossen

#endif
