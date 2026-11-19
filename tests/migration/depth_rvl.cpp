// The fixture only decodes frames made from bounded pixel arrays. The original
// RVL interface takes a pixel count and has no compressed input length.
#include "adapter.h"
#include "expected.h"
#include <cstdint>

struct Frame {
    const unsigned short *pixels;
    unsigned count;
    const unsigned int *words;
    unsigned word_count;
};
#include "vectors.h"

static_assert(sizeof(int) == 4 && sizeof(unsigned short) == 2);
static_assert(__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__);

// Static initialization supplies an initialized accumulator to both original
// implementations, including the upstream constructor with an empty body.
static compressed_depth_image_transport::RvlCodec codec;

static bool check(const Frame& frame) {
    unsigned short input[1024]{};
    unsigned short decoded[1026]{};
    int encoded[2050]{};
    for (unsigned i = 0; i < frame.count; ++i) input[i] = frame.pixels[i];
    constexpr int sentinel = 0x13572468;
    encoded[0] = encoded[2049] = sentinel;
    decoded[0] = decoded[frame.count + 1] = 0xaced;
    auto *bytes = reinterpret_cast<unsigned char*>(encoded + 1);
    int n = codec.CompressRVL(input, bytes, static_cast<int>(frame.count));
    if (n != static_cast<int>(4 * frame.word_count) ||
        encoded[0] != sentinel || encoded[2049] != sentinel) return false;
    for (unsigned i = 0; i < frame.word_count; ++i) {
        unsigned int expect = frame.words[i];
        if (ALTER_EXPECTATION && frame.count == 512 && i == 0) expect ^= 1;
        if (static_cast<unsigned int>(encoded[i + 1]) != expect) return false;
    }
    codec.DecompressRVL(bytes, decoded + 1, static_cast<int>(frame.count));
    for (unsigned i = 0; i < frame.count; ++i) {
        if (decoded[i + 1] != frame.pixels[i]) return false;
    }
    return decoded[0] == 0xaced && decoded[frame.count + 1] == 0xaced;
}

static int run_frames() {
    for (const Frame& frame : frames) if (!check(frame)) return 17;
    return 0;
}

#if defined(__wasm__)
extern "C" void _start() { if (run_frames() != 0) __builtin_trap(); }
#else
int main() { return run_frames(); }
#endif
