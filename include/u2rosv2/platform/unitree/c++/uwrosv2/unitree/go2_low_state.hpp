#pragma once
#include <stddef.h>
#include <stdint.h>

#if __cplusplus >= 201103L
# define UWROSV2_GO2_CPP_NOEXCEPT noexcept
#else
# define UWROSV2_GO2_CPP_NOEXCEPT throw()
#endif
#if __cplusplus >= 201402L
# define UWROSV2_GO2_CONSTEXPR14 constexpr
#else
# define UWROSV2_GO2_CONSTEXPR14
#endif
#if __cplusplus >= 202002L
# if __has_include(<array>) && __has_include(<bit>) && __has_include(<optional>) && __has_include(<span>)
#  include <array>
#  include <bit>
#  include <cstdint>
#  include <optional>
#  include <span>
#  define UWROSV2_GO2_STD20
# endif
#endif
#ifdef UWROSV2_GO2_STD20
# define UWROSV2_GO2_CONSTEXPR20 constexpr
#else
# define UWROSV2_GO2_CONSTEXPR20
#endif

namespace uwrosv2 { namespace unitree {

struct low_state {
    uint32_t tick;
    float first_joint_position;
};
enum { read_size = 48, result_size = 40 };

namespace detail {
typedef char requires_binary32[sizeof(float) == sizeof(uint32_t) ? 1 : -1];

inline UWROSV2_GO2_CONSTEXPR14 uint64_t go2_word(const uint8_t* bytes) UWROSV2_GO2_CPP_NOEXCEPT {
    uint64_t value = 0;
    for (unsigned i = 0; i < 8; ++i) value |= static_cast<uint64_t>(bytes[i]) << (8 * i);
    return value;
}

inline UWROSV2_GO2_CONSTEXPR20 float go2_position(uint32_t bits) UWROSV2_GO2_CPP_NOEXCEPT {
#ifdef UWROSV2_GO2_STD20
    return std::bit_cast<float>(bits);
#else
    float value;
    const unsigned char* from = reinterpret_cast<const unsigned char*>(&bits);
    unsigned char* to = reinterpret_cast<unsigned char*>(&value);
    for (size_t i = 0; i < sizeof value; ++i) to[i] = from[i];
    return value;
#endif
}
}

/** Write the six little-endian words in a Go2 driver.submit request. */
inline UWROSV2_GO2_CONSTEXPR14 bool encode_read(uint64_t sequence, uint64_t deadline_ns,
                                                 uint8_t* out, size_t capacity) UWROSV2_GO2_CPP_NOEXCEPT {
    if (!out || capacity < read_size) return false;
    const uint64_t words[] = {sequence, deadline_ns, 24, 1, 0, 16};
    for (size_t w = 0; w < 6; ++w)
        for (unsigned i = 0; i < 8; ++i)
            out[w * 8 + i] = static_cast<uint8_t>(words[w] >> (8 * i));
    return true;
}

/** Decode one complete driver.result. Commit the sample after validating all five words. */
inline UWROSV2_GO2_CONSTEXPR20 bool decode_result(const uint8_t* frame, size_t size, low_state& sample) UWROSV2_GO2_CPP_NOEXCEPT {
    if (!frame || size != result_size || detail::go2_word(frame) != 0 ||
        detail::go2_word(frame + 8) != 24 || detail::go2_word(frame + 16) != 16) return false;
    const uint64_t tick = detail::go2_word(frame + 24);
    const uint64_t bits = detail::go2_word(frame + 32);
    if (tick >> 32 || bits >> 32 || (bits & 0x7f800000u) == 0x7f800000u) return false;
    sample.tick = static_cast<uint32_t>(tick);
    sample.first_joint_position = detail::go2_position(static_cast<uint32_t>(bits));
    return true;
}

#ifdef UWROSV2_GO2_STD20
constexpr std::array<std::uint8_t, read_size> encode_read(std::uint64_t sequence, std::uint64_t deadline_ns) noexcept {
    std::array<std::uint8_t, read_size> request{};
    encode_read(sequence, deadline_ns, request.data(), request.size());
    return request;
}

constexpr std::optional<low_state> decode_result(std::span<const std::uint8_t> frame) noexcept {
    low_state sample{};
    if (!decode_result(frame.data(), frame.size(), sample)) return std::nullopt;
    return sample;
}
#endif

} }
#undef UWROSV2_GO2_CPP_NOEXCEPT
#undef UWROSV2_GO2_CONSTEXPR14
#undef UWROSV2_GO2_CONSTEXPR20
#undef UWROSV2_GO2_STD20
