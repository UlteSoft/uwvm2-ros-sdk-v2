/** Read-only projections of clearpath_dock_msgs/DockState. */
#ifndef UWROSV2_CLEARPATH_OBSERVATION_H
#define UWROSV2_CLEARPATH_OBSERVATION_H
#include "../../../../shared/reader.h"

enum { UWROSV2_CLEARPATH_UNDOCKED = 0 };
enum { UWROSV2_CLEARPATH_DOCKED = 1 };
enum { UWROSV2_CLEARPATH_IN_PROGRESS = 2 };
enum { UWROSV2_CLEARPATH_FAILED = 3 };
enum { UWROSV2_CLEARPATH_CANCELLED = 4 };
static const uwrosv2_obs_field uwrosv2_clearpath_observation_layout[] = {
    {1, 1, 0}, /* state */
};

/** Read state. Commit the output on success. */
static inline int uwrosv2_clearpath_read_state(const uint8_t *data, size_t size, uint8_t *out) UWROSV2_OBS_NOEXCEPT {
    if (!out) return 0;
    uint64_t bits;
    if (!uwrosv2_obs_project(data, size, 0, uwrosv2_clearpath_observation_layout,
                            sizeof uwrosv2_clearpath_observation_layout / sizeof uwrosv2_clearpath_observation_layout[0], 0, 0, &bits)) return 0;
    *out = (uint8_t)bits;
    return 1;
}

#endif
