/* Bounds-checked reader for platform observation fields. All offsets are relative
 * to the encoded body, so CDR alignment does not include its four-byte header. */
#ifndef UWROSV2_OBSERVATION_READER_H
#define UWROSV2_OBSERVATION_READER_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#if defined(__cplusplus) && __cplusplus >= 201103L
# define UWROSV2_OBS_NOEXCEPT noexcept
#elif defined(__cplusplus)
# define UWROSV2_OBS_NOEXCEPT throw()
#else
# define UWROSV2_OBS_NOEXCEPT
#endif

enum { UWROSV2_OBS_PACKED, UWROSV2_OBS_CDR, UWROSV2_OBS_FOURIER, UWROSV2_OBS_QUATERNION };
enum { UWROSV2_OBS_NUMBER, UWROSV2_OBS_BOOL, UWROSV2_OBS_MOTOR_COUNT };
typedef struct {
    uint8_t width; /* zero is a counted string */
    int16_t repeat; /* positive fixed size, 0 sequence, -1 saved count, <-1 remaining groups */
    uint8_t kind;
} uwrosv2_obs_field;
typedef struct {
    const uint8_t *body;
    size_t size, offset;
    int cdr, big;
} uwrosv2_obs_cursor;

static inline uint64_t uwrosv2_obs_word(const uint8_t *p, unsigned width, int big) UWROSV2_OBS_NOEXCEPT {
    uint64_t result = 0;
    for (unsigned i = 0; i < width; ++i)
        result |= (uint64_t)p[big ? width - 1 - i : i] << (8 * i);
    return result;
}

static inline int uwrosv2_obs_take(uwrosv2_obs_cursor *r, size_t count, unsigned width,
                                   const uint8_t **data) UWROSV2_OBS_NOEXCEPT {
    size_t padding = r->cdr ? ((0u - r->offset) & (width - 1u)) : 0u;
    if (padding > r->size - r->offset) return 0;
    r->offset += padding;
    if (count > (r->size - r->offset) / width) return 0;
    *data = r->body + r->offset;
    r->offset += count * width;
    return 1;
}

static inline int uwrosv2_obs_count(uwrosv2_obs_cursor *r, size_t *count) UWROSV2_OBS_NOEXCEPT {
    const uint8_t *word;
    if (!uwrosv2_obs_take(r, 1, 4, &word)) return 0;
    *count = (size_t)uwrosv2_obs_word(word, 4, r->big);
    return 1;
}

static inline int uwrosv2_obs_strings(uwrosv2_obs_cursor *r, size_t count) UWROSV2_OBS_NOEXCEPT {
    if (count > (r->size - r->offset) / 4) return 0;
    for (size_t i = 0; i < count; ++i) {
        size_t length;
        const uint8_t *bytes;
        if (!uwrosv2_obs_count(r, &length) || !uwrosv2_obs_take(r, length, 1, &bytes)) return 0;
        if (r->cdr && (!length || bytes[length - 1])) return 0;
    }
    return 1;
}

static inline int uwrosv2_obs_project(const uint8_t *data, size_t size, unsigned format,
                                      const uwrosv2_obs_field *layout, size_t fields,
                                      size_t wanted, size_t index, uint64_t *result) UWROSV2_OBS_NOEXCEPT {
    if (!data || !result) return 0;
    int cdr = format == UWROSV2_OBS_CDR || (format == UWROSV2_OBS_QUATERNION && size != 32);
    int big = format == UWROSV2_OBS_FOURIER;
    size_t prefix = 0, tail = 0;
    if (cdr) {
        if (size < 4 || data[0] || data[1] > 1 || data[2] || data[3] > 3) return 0;
        big = !data[1];
        prefix = 4;
        tail = data[3];
    } else if (format == UWROSV2_OBS_FOURIER) {
        const uint64_t fingerprint = ((uint64_t)0x4abec52fu << 32) | 0x17edd11fu;
        if (size < 8 || uwrosv2_obs_word(data, 8, 1) != fingerprint) return 0;
        prefix = 8;
    }
    uwrosv2_obs_cursor r = {data + prefix, size - prefix, 0, cdr, big};
    size_t saved = 0;
    uint64_t value = 0;
    int found = 0;
    for (size_t j = 0; j < fields; ++j) {
        const uwrosv2_obs_field *f = layout + j;
        const uint8_t *elements;
        size_t count;
        if (f->repeat > 0) count = (size_t)f->repeat;
        else if (f->repeat == 0) {
            if (!uwrosv2_obs_count(&r, &count)) return 0;
        } else if (f->repeat == -1) count = saved;
        else {
            size_t stride = (size_t)(-1 - f->repeat) * f->width;
            if ((r.size - r.offset) % stride) return 0;
            count = (r.size - r.offset) / f->width;
        }
        if (!f->width) {
            if (!uwrosv2_obs_strings(&r, count)) return 0;
            continue;
        }
        if (!count) continue;
        if (!uwrosv2_obs_take(&r, count, f->width, &elements)) return 0;
        if (f->kind == UWROSV2_OBS_MOTOR_COUNT) {
            saved = (size_t)uwrosv2_obs_word(elements, 4, big);
            if (saved > INT32_MAX) return 0;
        } else if (f->kind == UWROSV2_OBS_BOOL) {
            for (size_t k = 0; k < count; ++k) if (elements[k] > 1) return 0;
        }
        if (j == wanted && index < count) {
            value = uwrosv2_obs_word(elements + index * f->width, f->width, big);
            found = 1;
        }
    }
    size_t left = r.size - r.offset;
    if (!found || (left != 0 && left != tail) || (tail && tail != ((0u - r.offset) & 3u))) return 0;
    *result = value;
    return 1;
}
#endif
