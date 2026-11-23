#ifndef UWROSV2_FRANKA_CDR_SEQUENCES_H
#define UWROSV2_FRANKA_CDR_SEQUENCES_H
#include "wire.h"

/** A sequence of float64. The elements borrow either a typed array or validated CDR storage. */
typedef struct {
    const double *values;
    size_t count;
    uwrosv2_franka_cdr_reader wire;
} uwrosv2_franka_cdr_float64_sequence;
typedef struct {
    const double *values;
    size_t remaining;
    uwrosv2_franka_cdr_reader wire;
} uwrosv2_franka_cdr_float64_sequence_iterator;

/** The caller keeps values[0..count) readable for the lifetime of this sequence. */
static inline uwrosv2_franka_cdr_float64_sequence uwrosv2_franka_cdr_float64_sequence_values(const double *values, size_t count) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    uwrosv2_franka_cdr_float64_sequence seq = {NULL, 0, {NULL, 0, 0, uwrosv2_franka_cdr_big_endian, 0}};
    seq.values = values;
    seq.count = count;
    return seq;
}

static inline uwrosv2_franka_cdr_float64_sequence_iterator uwrosv2_franka_cdr_float64_sequence_iter(const uwrosv2_franka_cdr_float64_sequence *seq) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    uwrosv2_franka_cdr_float64_sequence_iterator it = {seq->values, seq->count, seq->wire};
    return it;
}

/** Advance an iterator and assign one typed element on success. */
static inline int uwrosv2_franka_cdr_float64_sequence_next(uwrosv2_franka_cdr_float64_sequence_iterator *it, double *out) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    if (!it || !out || !it->remaining) return 0;
    if (it->values) {
        *out = *it->values++;
    } else {
        uwrosv2_franka_cdr_reader cursor = it->wire;
        double value;
        if (!cursor.data || !uwrosv2_franka_cdr_get_float64(&cursor, &value)) return 0;
        it->wire = cursor;
        *out = value;
    }
    --it->remaining;
    return 1;
}

static inline int uwrosv2_franka_cdr_float64_sequence_get(uwrosv2_franka_cdr_reader *r, uwrosv2_franka_cdr_float64_sequence *out, uint32_t bound) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    uint64_t count;
    if (!uwrosv2_franka_cdr_get_word(r, 4, &count) || count > bound || count > (r->size - r->pos) / 8u) return 0;
    uwrosv2_franka_cdr_reader start = *r;
    for (size_t i = 0; i < (size_t)count; ++i) {
        double value;
        if (!uwrosv2_franka_cdr_get_float64(r, &value)) return 0;
    }
    start.size = r->pos;
    out->values = NULL;
    out->count = (size_t)count;
    out->wire = start;
    return 1;
}

static inline int uwrosv2_franka_cdr_float64_sequence_put(uwrosv2_franka_cdr_writer *w, const uwrosv2_franka_cdr_float64_sequence *seq, uint32_t bound) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    if (seq->count > bound || !uwrosv2_franka_cdr_put_word(w, 4, seq->count)) return 0;
    if (seq->values) {
        for (size_t i = 0; i < seq->count; ++i) {
            if (!uwrosv2_franka_cdr_put_float64(w, &seq->values[i])) return 0;
        }
        return 1;
    }
    /* Re-encode against the destination alignment origin and byte order. */
    uwrosv2_franka_cdr_reader r = seq->wire;
    if (seq->count && !r.data) return 0;
    for (size_t i = 0; i < seq->count; ++i) {
        double value;
        if (!uwrosv2_franka_cdr_get_float64(&r, &value) || !uwrosv2_franka_cdr_put_float64(w, &value)) return 0;
    }
    return r.pos == r.size;
}

/** A sequence of string. The elements borrow either a typed array or validated CDR storage. */
typedef struct {
    const uwrosv2_franka_cdr_string *values;
    size_t count;
    uwrosv2_franka_cdr_reader wire;
} uwrosv2_franka_cdr_string_sequence;
typedef struct {
    const uwrosv2_franka_cdr_string *values;
    size_t remaining;
    uwrosv2_franka_cdr_reader wire;
} uwrosv2_franka_cdr_string_sequence_iterator;

/** The caller keeps values[0..count) readable for the lifetime of this sequence. */
static inline uwrosv2_franka_cdr_string_sequence uwrosv2_franka_cdr_string_sequence_values(const uwrosv2_franka_cdr_string *values, size_t count) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    uwrosv2_franka_cdr_string_sequence seq = {NULL, 0, {NULL, 0, 0, uwrosv2_franka_cdr_big_endian, 0}};
    seq.values = values;
    seq.count = count;
    return seq;
}

static inline uwrosv2_franka_cdr_string_sequence_iterator uwrosv2_franka_cdr_string_sequence_iter(const uwrosv2_franka_cdr_string_sequence *seq) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    uwrosv2_franka_cdr_string_sequence_iterator it = {seq->values, seq->count, seq->wire};
    return it;
}

/** Advance an iterator and assign one typed element on success. */
static inline int uwrosv2_franka_cdr_string_sequence_next(uwrosv2_franka_cdr_string_sequence_iterator *it, uwrosv2_franka_cdr_string *out) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    if (!it || !out || !it->remaining) return 0;
    if (it->values) {
        *out = *it->values++;
    } else {
        uwrosv2_franka_cdr_reader cursor = it->wire;
        uwrosv2_franka_cdr_string value;
        if (!cursor.data || !uwrosv2_franka_cdr_get_string(&cursor, &value)) return 0;
        it->wire = cursor;
        *out = value;
    }
    --it->remaining;
    return 1;
}

static inline int uwrosv2_franka_cdr_string_sequence_get(uwrosv2_franka_cdr_reader *r, uwrosv2_franka_cdr_string_sequence *out, uint32_t bound) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    uint64_t count;
    if (!uwrosv2_franka_cdr_get_word(r, 4, &count) || count > bound || count > (r->size - r->pos) / 5u) return 0;
    uwrosv2_franka_cdr_reader start = *r;
    for (size_t i = 0; i < (size_t)count; ++i) {
        uwrosv2_franka_cdr_string value;
        if (!uwrosv2_franka_cdr_get_string(r, &value)) return 0;
    }
    start.size = r->pos;
    out->values = NULL;
    out->count = (size_t)count;
    out->wire = start;
    return 1;
}

static inline int uwrosv2_franka_cdr_string_sequence_put(uwrosv2_franka_cdr_writer *w, const uwrosv2_franka_cdr_string_sequence *seq, uint32_t bound) UWROSV2_FRANKA_CDR_C_NOEXCEPT {
    if (seq->count > bound || !uwrosv2_franka_cdr_put_word(w, 4, seq->count)) return 0;
    if (seq->values) {
        for (size_t i = 0; i < seq->count; ++i) {
            if (!uwrosv2_franka_cdr_put_string(w, &seq->values[i])) return 0;
        }
        return 1;
    }
    /* Re-encode against the destination alignment origin and byte order. */
    uwrosv2_franka_cdr_reader r = seq->wire;
    if (seq->count && !r.data) return 0;
    for (size_t i = 0; i < seq->count; ++i) {
        uwrosv2_franka_cdr_string value;
        if (!uwrosv2_franka_cdr_get_string(&r, &value) || !uwrosv2_franka_cdr_put_string(w, &value)) return 0;
    }
    return r.pos == r.size;
}

#endif
