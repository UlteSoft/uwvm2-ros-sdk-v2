/* Allocation-free primitives for the ABB ROS 1 message and service bodies. */
#ifndef UWROSV2_ABB_ROS1_WIRE_H
#define UWROSV2_ABB_ROS1_WIRE_H
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#ifndef UWROSV2_ABB_ROS1_NOEXCEPT
# if defined(__cplusplus) && __cplusplus >= 201103L
#  define UWROSV2_ABB_ROS1_NOEXCEPT noexcept
# elif defined(__cplusplus)
#  define UWROSV2_ABB_ROS1_NOEXCEPT throw()
# else
#  define UWROSV2_ABB_ROS1_NOEXCEPT
# endif
#endif

/** ROS 1 string payload. Embedded NULs are valid. The borrowed bytes need no terminator. */
typedef struct {
    const uint8_t *data; /**< Readable bytes. May be null when size is zero. */
    size_t size;         /**< Byte count, representable as a ROS uint32. */
} uwrosv2_abb_ros1_string;
/** Standard two-word ROS 1 timestamp. */
typedef struct {
    uint32_t sec;  /**< Seconds since the ROS time epoch. */
    uint32_t nsec; /**< Nanoseconds within the indicated second. */
} uwrosv2_abb_ros1_time;

/** @cond INTERNAL */
typedef struct { const uint8_t *data; size_t size, pos; } uwrosv2_abb_ros1_reader;
typedef struct { uint8_t *data; size_t capacity, pos; } uwrosv2_abb_ros1_writer;
typedef char uwrosv2_abb_ros1_float_widths[(sizeof(float) == 4 && sizeof(double) == 8) ? 1 : -1];

/* A null writer data pointer counts bytes. Skip pointer arithmetic on null empty buffers. */
static inline int uwrosv2_abb_ros1_get_bytes(uwrosv2_abb_ros1_reader *r, size_t size,
                                             const uint8_t **out) UWROSV2_ABB_ROS1_NOEXCEPT {
    if (r->pos > r->size || size > r->size - r->pos || (size && !r->data)) return 0;
    *out = r->data ? r->data + r->pos : NULL;
    r->pos += size;
    return 1;
}

static inline int uwrosv2_abb_ros1_put_bytes(uwrosv2_abb_ros1_writer *w, const uint8_t *data,
                                             size_t size) UWROSV2_ABB_ROS1_NOEXCEPT {
    if (w->pos > w->capacity || size > w->capacity - w->pos || (size && !data)) return 0;
    if (w->data && size) memcpy(w->data + w->pos, data, size);
    w->pos += size;
    return 1;
}

static inline int uwrosv2_abb_ros1_get_word(uwrosv2_abb_ros1_reader *r, size_t width,
                                            uint64_t *out) UWROSV2_ABB_ROS1_NOEXCEPT {
    const uint8_t *bytes;
    uint64_t word = 0;
    size_t i;
    if (width > sizeof word || !uwrosv2_abb_ros1_get_bytes(r, width, &bytes)) return 0;
    for (i = 0; i < width; ++i) word |= (uint64_t)bytes[i] << (8 * i);
    *out = word;
    return 1;
}

static inline int uwrosv2_abb_ros1_put_word(uwrosv2_abb_ros1_writer *w, size_t width,
                                            uint64_t word) UWROSV2_ABB_ROS1_NOEXCEPT {
    size_t i;
    if (width > sizeof word || w->pos > w->capacity || width > w->capacity - w->pos) return 0;
    if (w->data) {
        for (i = 0; i < width; ++i) w->data[w->pos + i] = (uint8_t)(word >> (8 * i));
    }
    w->pos += width;
    return 1;
}

#define UWROSV2_ABB_ROS1_UNSIGNED(NAME, TYPE, WIDTH) \
static inline int uwrosv2_abb_ros1_get_##NAME(uwrosv2_abb_ros1_reader *r, TYPE *out) UWROSV2_ABB_ROS1_NOEXCEPT { \
    uint64_t word; \
    if (!uwrosv2_abb_ros1_get_word(r, WIDTH, &word)) return 0; \
    *out = (TYPE)word; \
    return 1; \
} \
static inline int uwrosv2_abb_ros1_put_##NAME(uwrosv2_abb_ros1_writer *w, const TYPE *v) UWROSV2_ABB_ROS1_NOEXCEPT { \
    return uwrosv2_abb_ros1_put_word(w, WIDTH, *v); \
}
UWROSV2_ABB_ROS1_UNSIGNED(uint8, uint8_t, 1)
UWROSV2_ABB_ROS1_UNSIGNED(uint16, uint16_t, 2)
UWROSV2_ABB_ROS1_UNSIGNED(uint32, uint32_t, 4)
#undef UWROSV2_ABB_ROS1_UNSIGNED

static inline int uwrosv2_abb_ros1_get_bool(uwrosv2_abb_ros1_reader *r, uint8_t *out) UWROSV2_ABB_ROS1_NOEXCEPT {
    return uwrosv2_abb_ros1_get_uint8(r, out) && *out <= 1;
}

static inline int uwrosv2_abb_ros1_put_bool(uwrosv2_abb_ros1_writer *w, const uint8_t *v) UWROSV2_ABB_ROS1_NOEXCEPT {
    return *v <= 1 && uwrosv2_abb_ros1_put_uint8(w, v);
}

#define UWROSV2_ABB_ROS1_FLOAT(NAME, TYPE, WORD) \
static inline int uwrosv2_abb_ros1_get_##NAME(uwrosv2_abb_ros1_reader *r, TYPE *out) UWROSV2_ABB_ROS1_NOEXCEPT { \
    uint64_t bits; \
    WORD word; \
    if (!uwrosv2_abb_ros1_get_word(r, sizeof word, &bits)) return 0; \
    word = (WORD)bits; \
    memcpy(out, &word, sizeof word); \
    return 1; \
} \
static inline int uwrosv2_abb_ros1_put_##NAME(uwrosv2_abb_ros1_writer *w, const TYPE *v) UWROSV2_ABB_ROS1_NOEXCEPT { \
    WORD word; \
    memcpy(&word, v, sizeof word); \
    return uwrosv2_abb_ros1_put_word(w, sizeof word, word); \
}
UWROSV2_ABB_ROS1_FLOAT(float32, float, uint32_t)
UWROSV2_ABB_ROS1_FLOAT(float64, double, uint64_t)
#undef UWROSV2_ABB_ROS1_FLOAT

static inline int uwrosv2_abb_ros1_get_string(uwrosv2_abb_ros1_reader *r,
                                              uwrosv2_abb_ros1_string *out) UWROSV2_ABB_ROS1_NOEXCEPT {
    uint32_t length;
    if (!uwrosv2_abb_ros1_get_uint32(r, &length) ||
        !uwrosv2_abb_ros1_get_bytes(r, length, &out->data)) return 0;
    out->size = length;
    return 1;
}
static inline int uwrosv2_abb_ros1_put_string(uwrosv2_abb_ros1_writer *w,
                                              const uwrosv2_abb_ros1_string *v) UWROSV2_ABB_ROS1_NOEXCEPT {
    return v->size == (uint32_t)v->size && uwrosv2_abb_ros1_put_word(w, 4, v->size)
        && uwrosv2_abb_ros1_put_bytes(w, v->data, v->size);
}
static inline int uwrosv2_abb_ros1_get_time(uwrosv2_abb_ros1_reader *r,
                                            uwrosv2_abb_ros1_time *out) UWROSV2_ABB_ROS1_NOEXCEPT {
    return uwrosv2_abb_ros1_get_uint32(r, &out->sec) && uwrosv2_abb_ros1_get_uint32(r, &out->nsec);
}
static inline int uwrosv2_abb_ros1_put_time(uwrosv2_abb_ros1_writer *w,
                                            const uwrosv2_abb_ros1_time *v) UWROSV2_ABB_ROS1_NOEXCEPT {
    return uwrosv2_abb_ros1_put_uint32(w, &v->sec) && uwrosv2_abb_ros1_put_uint32(w, &v->nsec);
}
/** @endcond */

#endif
