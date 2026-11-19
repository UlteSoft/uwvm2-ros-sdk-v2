#include "tf2/buffer_core.hpp"
#include "tf2/exceptions.hpp"
#include <chrono>
#include <cmath>
#include <string>
#include <sstream>
#if defined(WROS_TF2_THREADED)
#include <atomic>
#include <thread>
#endif

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

static bool check_yaml() {
    const std::u16string characters{0, u'A', u'"', u'\\', 0x80, 0x03a9, 0xd800, 0xdc00};
    std::ostringstream out;
    rosidl_generator_traits::value_to_yaml(characters, out);
    // Jazzy emits raw ASCII, skips embedded NUL and escapes each non-ASCII code unit.
    return out.str() == "\"A\"\\\\x80\\u03a9\\ud800\\udc00\"";
}

#if defined(WROS_TF2_SINGLE_EXECUTOR)
static bool check_lock() {
    wros_tf2::single_executor_mutex mutex;
    try {
        std::unique_lock outer(mutex);
        try {
            std::unique_lock nested(mutex);
            return false;
        } catch (const std::logic_error&) {}
        throw 42;
    } catch (int value) {
        if (value != 42) return false;
    }
    std::unique_lock after_unwind(mutex);
    return after_unwind.owns_lock();
}
#endif

#if defined(WROS_TF2_THREADED)
static bool check_parallel() {
    tf2::BufferCore buffer(10s);
    if (!insert(buffer, "map", "camera", 1, 2, 0, 1, true)) return false;
    std::atomic<bool> ready{false}, valid{true};
    auto reader = [&] {
        while (!ready.load(std::memory_order_acquire)) std::this_thread::yield();
        for (unsigned i = 0; i < 512; ++i) {
            const auto pose = buffer.lookupTransform("map", "camera", stamp(1));
            const auto x = pose.transform.translation.x;
            if (x != 2 && x != 3) valid.store(false);
        }
    };
    std::thread first(reader), second(reader);
    ready.store(true, std::memory_order_release);
    for (unsigned i = 0; i < 512; ++i)
        if (!insert(buffer, "map", "camera", 1, 2 + (i & 1), 0, 1, true)) valid.store(false);
    first.join();
    second.join();
    return valid.load();
}
#endif

static int check_buffer() {
    if (!check_yaml()) return 11;
#if defined(WROS_TF2_SINGLE_EXECUTOR)
    if (!check_lock()) return 12;
#elif defined(WROS_TF2_THREADED)
    if (!check_parallel()) return 13;
#endif
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
