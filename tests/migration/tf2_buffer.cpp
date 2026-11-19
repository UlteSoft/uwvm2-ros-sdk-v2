#include "tf2/buffer_core.hpp"
#include "tf2/exceptions.hpp"
#include <chrono>
#include <cmath>
#include <string>

using namespace std::chrono_literals;

static bool insert(tf2::BufferCore& buffer, const char* parent, const char* child,
                   int second, double x, double z, double w, bool fixed = false) {
    geometry_msgs::msg::TransformStamped t;
    t.header.frame_id = parent;
    t.child_frame_id = child;
    t.header.stamp.sec = second;
    t.transform.translation.x = x;
    t.transform.rotation.z = z;
    t.transform.rotation.w = w;
    return buffer.setTransform(t, "qualified-clock", fixed);
}

static tf2::TimePoint stamp(int second) { return tf2::TimePoint(std::chrono::seconds(second)); }

static bool close(double a, double b) { return std::abs(a - b) < 1e-9; }

static int check_buffer() {
    tf2::BufferCore buffer(10s);
    // Odom->base moves linearly by 2m and rotates by a half turn in 2s.
    // Base->camera is a fixed 1m offset on the robot's forward axis.
    if (!insert(buffer, "odom", "base", 20, 2, 1, 0) ||
        !insert(buffer, "odom", "base", 18, 0, 0, 1) ||
        !insert(buffer, "base", "camera", 1, 1, 0, 1, true) ||
        !insert(buffer, "island", "detached", 19, 0, 0, 1, true)) return 2;
    auto query = [&](tf2::TimePoint time) {
        return buffer.lookupTransform("odom", "camera", time);
    };
    auto sample = query(stamp(19));
    if (sample.header.stamp.sec != 19 || sample.header.frame_id != "odom" ||
        sample.child_frame_id != "camera" || !close(sample.transform.translation.x, 1 + WROS_CHANGED_REFERENCE) ||
        !close(sample.transform.translation.y, 1) ||
        !close(std::abs(sample.transform.rotation.z), std::sqrt(0.5))) return 3;
    auto latest = query(tf2::TimePointZero);
    if (latest.header.stamp.sec != 20 || !close(latest.transform.translation.x, 1)) return 4;
    if (!buffer.canTransform("odom","camera",stamp(18),nullptr) ||
         buffer.canTransform("odom","camera",stamp(21),nullptr) ||
         buffer.canTransform("odom","detached",stamp(19),nullptr)) return 5;
    try { (void)query(stamp(21)); return 6; }
    catch (const tf2::ExtrapolationException&) {}
    try { (void)buffer.lookupTransform("odom","detached",stamp(19)); return 7; }
    catch (const tf2::ConnectivityException&) {}
    // Populate recent dynamic samples and allow TimeCache to prune the old segment.
    if (!insert(buffer,"odom","base",40,4,0,1) ||
        !insert(buffer,"odom","base",41,5,0,1)) return 8;
    try { (void)query(stamp(19)); return 9; }
    catch (const tf2::ExtrapolationException&) {}
    buffer.clear();
    if (buffer.canTransform("odom","camera",stamp(41),nullptr)) return 10;
    return 0;
}

#if defined(__wasm__)
extern "C" void _start() { if (check_buffer()) __builtin_trap(); }
#else
int main() { return check_buffer(); }
#endif
