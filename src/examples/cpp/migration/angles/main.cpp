/** @file Exercise the ROS angles library's wraparound calculation in a guest. */
#include <uwrosv2/scene.hpp>
#include "upstream/angles.h"

extern "C" void _start() UWROSV2_CPP_NOEXCEPT {
    volatile double from = 170.0;
    volatile double to = -170.0;
    const double delta = angles::shortest_angular_distance(
        angles::from_degrees(from), angles::from_degrees(to));
    if (uwrosv2::abi() != 2 || std::abs(angles::to_degrees(delta) - 20.0) > 1e-9)
        __builtin_trap();
}
