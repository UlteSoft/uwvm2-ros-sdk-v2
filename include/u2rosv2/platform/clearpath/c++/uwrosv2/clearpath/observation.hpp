/** Read-only projections of clearpath_dock_msgs/DockState. */
#ifndef UWROSV2_CLEARPATH_OBSERVATION_HPP
#define UWROSV2_CLEARPATH_OBSERVATION_HPP
#include "../../../../shared/reader.h"

namespace uwrosv2 { namespace clearpath {

enum { undocked = 0 };
enum { docked = 1 };
enum { in_progress = 2 };
enum { failed = 3 };
enum { cancelled = 4 };
static const uwrosv2_obs_field observation_layout[] = {
    {1, 1, 0}, /* state */
};

/** Read state. Commit the output on success. */
static inline bool read_state(const uint8_t *data, size_t size, uint8_t &out) UWROSV2_OBS_NOEXCEPT {
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, observation_layout,
                            sizeof observation_layout / sizeof observation_layout[0], 0, 0, &bits)) return 0;
    out = (uint8_t)bits;
    return 1;
}

} } // namespace uwrosv2::clearpath

#endif
