/** Encapsulated XCDRv1 messages in caller-owned storage. Supports C++98 and later. */
#ifndef UWROSV2_UNIVERSAL_ROBOTS_CDR_CODEC_HPP
#define UWROSV2_UNIVERSAL_ROBOTS_CDR_CODEC_HPP
#include "wire.hpp"

namespace uwrosv2 { namespace universal_robots { namespace cdr {

template<class T> struct value_codec;

/** Measure the canonical frame including its four-byte encapsulation. */
template<class T>
inline bool encoded_size(const T &value, size_t &size) UWROSV2_UNIVERSAL_ROBOTS_CDR_NOEXCEPT {
    writer measure = {NULL, static_cast<size_t>(-1) - 4, 0, little_endian};
    if (!value_codec<T>::put(&measure, &value)) return false;
    size = 4 + measure.pos;
    return true;
}

/** Encode into storage disjoint from the value, its borrowed spans and the count slot. */
template<class T>
inline bool encode(const T &value, endian order, uint8_t *out, size_t capacity,
                   size_t &written) UWROSV2_UNIVERSAL_ROBOTS_CDR_NOEXCEPT {
    size_t size;
    if (!out || (order != little_endian && order != big_endian) ||
        !encoded_size(value, size) || size > capacity) return false;
    writer destination = {out + 4, size - 4, 0, order};
    if (!value_codec<T>::put(&destination, &value)) return false;
    write_header(out, order);
    written = size;
    return true;
}

/** Validate the full frame before assigning out. Decoded strings borrow the immutable frame. */
template<class T>
inline bool decode(const uint8_t *frame, size_t size, T &out) UWROSV2_UNIVERSAL_ROBOTS_CDR_NOEXCEPT {
    reader cursor;
    T value;
    if (!begin_read(&cursor, frame, size) || !value_codec<T>::get(&cursor, &value) || !end_read(&cursor))
        return false;
    out = value;
    return true;
}

/** Check the complete encapsulated frame using the named message type. */
template<class T>
inline bool validate(const uint8_t *frame, size_t size) UWROSV2_UNIVERSAL_ROBOTS_CDR_NOEXCEPT {
    reader cursor;
    T value;
    return begin_read(&cursor, frame, size) && value_codec<T>::get(&cursor, &value) && end_read(&cursor);
}

} } } // namespace uwrosv2::universal_robots::cdr
#endif
