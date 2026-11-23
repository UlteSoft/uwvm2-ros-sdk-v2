#ifndef UWROSV2_UNITREE_GO2_LOW_STATE_H
#define UWROSV2_UNITREE_GO2_LOW_STATE_H

#include <stddef.h>
#include <stdint.h>

#if defined(__cplusplus) && __cplusplus >= 201103L
# define UWROSV2_GO2_NOEXCEPT noexcept
#elif defined(__cplusplus)
# define UWROSV2_GO2_NOEXCEPT throw()
#else
# define UWROSV2_GO2_NOEXCEPT
#endif

typedef struct {
    uint32_t tick;
    float first_joint_position;
} uwrosv2_go2_low_state;

enum { UWROSV2_GO2_READ_BYTES = 48, UWROSV2_GO2_RESULT_BYTES = 40 };
typedef char uwrosv2_go2_requires_binary32[sizeof(float) == sizeof(uint32_t) ? 1 : -1];

static inline uint64_t uwrosv2_go2_read_word(const uint8_t *bytes) UWROSV2_GO2_NOEXCEPT {
    uint64_t word = 0;
    for (unsigned i = 0; i < 8; ++i) word |= (uint64_t)bytes[i] << (8u * i);
    return word;
}

/** Write the driver.submit envelope for one buffer.read request. */
static inline int uwrosv2_go2_encode_read(uint64_t sequence, uint64_t deadline_ns, uint8_t *out, size_t capacity) UWROSV2_GO2_NOEXCEPT {
    if (!out || capacity < UWROSV2_GO2_READ_BYTES) return 0;
    const uint64_t words[] = {sequence, deadline_ns, 24, 1, 0, 16};
    for (unsigned w = 0; w < 6; ++w)
        for (unsigned i = 0; i < 8; ++i) out[8 * w + i] = (uint8_t)(words[w] >> (8u * i));
    return 1;
}

/** Decode the complete 40-byte successful driver.result. Output is committed only on success. */
static inline int uwrosv2_go2_decode_result(const uint8_t *reply, size_t size, uwrosv2_go2_low_state *out) UWROSV2_GO2_NOEXCEPT {
    if (!reply || !out || size != UWROSV2_GO2_RESULT_BYTES) return 0;
    if (uwrosv2_go2_read_word(reply) != 0 || uwrosv2_go2_read_word(reply + 8) != 24 ||
        uwrosv2_go2_read_word(reply + 16) != 16) return 0;
    const uint64_t tick = uwrosv2_go2_read_word(reply + 24);
    const uint64_t bits = uwrosv2_go2_read_word(reply + 32);
    if (tick >> 32 || bits >> 32 || (bits & 0x7f800000u) == 0x7f800000u) return 0;
    const uint32_t word = (uint32_t)bits;
    uwrosv2_go2_low_state sample = {(uint32_t)tick, 0};
    const unsigned char *src = (const unsigned char *)&word;
    unsigned char *dst = (unsigned char *)&sample.first_joint_position;
    for (size_t i = 0; i < sizeof word; ++i) dst[i] = src[i];
    *out = sample;
    return 1;
}

#undef UWROSV2_GO2_NOEXCEPT
#endif
