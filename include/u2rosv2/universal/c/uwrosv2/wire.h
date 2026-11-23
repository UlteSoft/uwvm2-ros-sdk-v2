/** @file Allocation-free writers and readers for guest-owned record storage.
 *  Every scalar is little endian. Canonical text and blobs carry a u64 byte
 *  length. Fixed artifact digests and payloads use the raw-byte operation.
 *  Keep source fields disjoint from the writer's scratch space. */
#ifndef UWROSV2_C_WIRE_H
#define UWROSV2_C_WIRE_H
#include "base.h"

typedef struct { uwrosv2_output storage; size_t used; uint32_t status; } uwrosv2_writer;
typedef struct { uwrosv2_input storage; size_t used; uint32_t status; } uwrosv2_reader;

static inline uwrosv2_writer uwrosv2_writer_init(uwrosv2_output storage) UWROSV2_C_NOEXCEPT {
    uwrosv2_writer value = {storage, 0, storage.size && !storage.data ? 22u : 0u}; return value;
}
static inline int uwrosv2_writer_room(uwrosv2_writer *w, size_t count) UWROSV2_C_NOEXCEPT {
    if (!w || w->status) return 0;
    if (count <= w->storage.size - w->used) return 1;
    w->status = 90; return 0;
}
static inline void uwrosv2_write_word(uwrosv2_writer *w, uint64_t value) UWROSV2_C_NOEXCEPT {
    if (!uwrosv2_writer_room(w, 8)) return;
    uwrosv2_write_le64(w->storage.data + w->used, value); w->used += 8;
}
static inline void uwrosv2_write_raw(uwrosv2_writer *w, uwrosv2_input bytes) UWROSV2_C_NOEXCEPT {
    if (!uwrosv2_writer_room(w, bytes.size)) return;
    if (bytes.size && !bytes.data) { w->status = 22; return; }
    for (size_t i = 0; i < bytes.size; ++i) w->storage.data[w->used + i] = bytes.data[i];
    w->used += bytes.size;
}
static inline void uwrosv2_write_blob(uwrosv2_writer *w, uwrosv2_input bytes) UWROSV2_C_NOEXCEPT {
    if (!w || w->status) return;
    if ((bytes.size && !bytes.data) || bytes.size > (size_t)-1 - 8) { w->status = 22; return; }
    if (!uwrosv2_writer_room(w, 8 + bytes.size)) return;
    uwrosv2_write_word(w, bytes.size); uwrosv2_write_raw(w, bytes);
}
/** Supply UTF-8 without a terminating NUL. The selected VM decoder checks the text. */
static inline void uwrosv2_write_text(uwrosv2_writer *w, uwrosv2_text text) UWROSV2_C_NOEXCEPT {
    uwrosv2_write_blob(w, uwrosv2_bytes(text.data, text.size));
}
static inline uwrosv2_input uwrosv2_written(const uwrosv2_writer *w) UWROSV2_C_NOEXCEPT {
    return uwrosv2_bytes(w->storage.data, w->status ? 0 : w->used);
}

static inline uwrosv2_reader uwrosv2_reader_init(uwrosv2_input storage) UWROSV2_C_NOEXCEPT {
    uwrosv2_reader value = {storage, 0, storage.size && !storage.data ? 22u : 0u}; return value;
}
static inline int uwrosv2_read_word(uwrosv2_reader *r, uint64_t *out) UWROSV2_C_NOEXCEPT {
    if (!r || r->status) return 0;
    if (!out || r->storage.size - r->used < 8) { r->status = 22; return 0; }
    *out = uwrosv2_read_le64(r->storage.data + r->used); r->used += 8; return 1;
}
/** Borrow the returned payload from the original input for its remaining lifetime. */
static inline int uwrosv2_read_blob(uwrosv2_reader *r, uwrosv2_input *out) UWROSV2_C_NOEXCEPT {
    uint64_t size;
    if (!r || r->status) return 0;
    if (!out || !uwrosv2_read_word(r, &size) || size > r->storage.size - r->used) {
        r->status = 22; return 0;
    }
    *out = uwrosv2_bytes(r->storage.data + r->used, (size_t)size); r->used += (size_t)size; return 1;
}
static inline int uwrosv2_reader_done(const uwrosv2_reader *r) UWROSV2_C_NOEXCEPT {
    return r && r->status == 0 && r->used == r->storage.size;
}
#endif
