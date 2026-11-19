// Compile directly against the selected upstream ROS header.
// Several ROS 1 headers use ::atoi without including its declaration.
#include <stdlib.h>
#include "adapter.h"
#include "expected.h"
#include <stdexcept>
#include <string>

enum class Kind { mono, color, alpha, bayer, generic };
struct Encoding {
    const char* name;
    int channels;
    int bits;
    Kind kind;
};
#include "vectors.h"

static bool unknown_format(const std::string& name) {
    namespace enc = sensor_msgs::image_encodings;
    for (const auto query : {enc::numChannels, enc::bitDepth}) {
        try {
            (void)query(name);
            return false;
        } catch (const std::runtime_error&) {}
    }
    return true;
}

static int probe() {
    namespace enc = sensor_msgs::image_encodings;
    for (const auto& entry : cases) {
        const std::string name(entry.name);
        if (FOUR_CHANNEL_LAYOUTS_ONLY && entry.channels > 4) {
            if (!unknown_format(name)) return 17;
            continue;
        }
        const bool color = entry.kind == Kind::color || entry.kind == Kind::alpha;
        if (enc::isColor(name) != color || enc::isMono(name) != (entry.kind == Kind::mono) ||
            enc::hasAlpha(name) != (entry.kind == Kind::alpha) || enc::isBayer(name) != (entry.kind == Kind::bayer) ||
            enc::numChannels(name) != entry.channels || enc::bitDepth(name) != entry.bits + ALTER_EXPECTATION)
            return 17;
    }
    return unknown_format("unregistered_image_format") ? 0 : 17;
}

#ifdef __wasm__
extern "C" void __wasm_call_ctors();
extern "C" void _start() {
    __wasm_call_ctors();
    if (probe() != 0) __builtin_trap();
}
#else
int main() { return probe(); }
#endif
