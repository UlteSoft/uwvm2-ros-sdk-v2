#include "tf2/time_cache.hpp"
#include <chrono>
#include <cmath>

using namespace std::chrono_literals;

static tf2::TimePoint at(int seconds) { return tf2::TimePoint(std::chrono::seconds(seconds)); }

static tf2::TransformStorage pose(int sec, double x, bool rotated = false) {
    return {at(sec), rotated ? tf2::Quaternion(0, 0, 1, 0) : tf2::Quaternion(0, 0, 0, 1),
            tf2::Vector3(x, 0, 0), 1, 2};
}

static int check_cache() {
    tf2::TimeCache cache(10s);
    tf2::TransformStorage out;
    if (!cache.insertData(pose(20, 2, true)) || !cache.insertData(pose(18, 0))) return 2;
    if (!cache.getData(at(19), out) || out.frame_id_ != 1 || out.child_frame_id_ != 2 ||
        std::abs(out.translation_.x() - (1 + WROS_CHANGED_REFERENCE)) > 1e-9 ||
        std::abs(std::abs(out.rotation_.z()) - std::sqrt(0.5)) > 1e-9) return 3;
    if (!cache.getData(tf2::TimePointZero, out) || out.stamp_ != at(20)) return 4;
    tf2::TF2Error error{};
    if (cache.getData(at(22), out, nullptr, &error) ||
        error != tf2::TF2Error::TF2_FORWARD_EXTRAPOLATION_ERROR) return 5;
    if (!cache.insertData(pose(40, 4)) || !cache.insertData(pose(41, 5))) return 6;
    if (cache.getData(at(19), out, nullptr, &error) ||
        error != tf2::TF2Error::TF2_BACKWARD_EXTRAPOLATION_ERROR) return 7;
    cache.clearList();
    if (cache.getListLength() || cache.getData(at(41), out)) return 8;
    return 0;
}

#if defined(__wasm__)
extern "C" void _start() { if (check_cache()) __builtin_trap(); }
#else
int main() { return check_cache(); }
#endif
