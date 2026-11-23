/** Allocation-free XCDRv1 sequences and framed messages for C++98 and later. */
#ifndef UWROSV2_FRANKA_CDR_CODEC_HPP
#define UWROSV2_FRANKA_CDR_CODEC_HPP
#include "wire.hpp"

namespace uwrosv2 { namespace franka { namespace cdr {

/** Borrowed sequence of typed values or validated wire elements. Keep its backing storage readable. */
template<class T>
class Sequence {
    const T *values_;
    size_t count_;
    reader wire_;
public:
    Sequence() UWROSV2_FRANKA_CDR_NOEXCEPT : values_(NULL), count_(0), wire_() {}

    static Sequence from_values(const T *values, size_t count) UWROSV2_FRANKA_CDR_NOEXCEPT {
        Sequence result;
        result.values_ = values;
        result.count_ = count;
        return result;
    }

    size_t size() const UWROSV2_FRANKA_CDR_NOEXCEPT { return count_; }

    class iterator {
        const T *values_;
        size_t remaining_;
        reader wire_;
    public:
        explicit iterator(const Sequence &seq) UWROSV2_FRANKA_CDR_NOEXCEPT
            : values_(seq.values_), remaining_(seq.count_), wire_(seq.wire_) {}

        bool next(T &out) UWROSV2_FRANKA_CDR_NOEXCEPT {
            if (!remaining_) return false;
            if (values_) {
                out = *values_++;
            } else {
                T value;
                reader cursor = wire_;
                if (!cursor.data || !value_codec<T>::get(&cursor, &value)) return false;
                out = value;
                wire_ = cursor;
            }
            --remaining_;
            return true;
        }
    };

    iterator iter() const UWROSV2_FRANKA_CDR_NOEXCEPT { return iterator(*this); }

    static bool get(reader *r, Sequence *out, uint32_t bound) UWROSV2_FRANKA_CDR_NOEXCEPT {
        uint64_t count;
        if (!get_word(r, 4, &count) || count > bound ||
            count > (r->size - r->pos) / value_codec<T>::minimum_size) return false;
        reader start = *r;
        for (size_t i = 0; i < count; ++i) {
            T element;
            if (!value_codec<T>::get(r, &element)) return false;
        }
        start.size = r->pos;
        out->values_ = NULL;
        out->count_ = static_cast<size_t>(count);
        out->wire_ = start;
        return true;
    }

    bool put(writer *w, uint32_t bound) const UWROSV2_FRANKA_CDR_NOEXCEPT {
        if (count_ > bound || !put_word(w, 4, count_)) return false;
        if (values_) {
            for (size_t i = 0; i < count_; ++i) {
                if (!value_codec<T>::put(w, &values_[i])) return false;
            }
            return true;
        }
        reader cursor = wire_;
        if (count_ && !cursor.data) return false;
        for (size_t i = 0; i < count_; ++i) {
            T element;
            if (!value_codec<T>::get(&cursor, &element) || !value_codec<T>::put(w, &element)) return false;
        }
        return cursor.pos == cursor.size;
    }
};

/** Measure the full encapsulated frame and assign its size on success. */
template<class T>
inline bool encoded_size(const T &value, size_t &size) UWROSV2_FRANKA_CDR_NOEXCEPT {
    writer measure = {NULL, static_cast<size_t>(-1) - 4, 0, little_endian};
    if (!value_codec<T>::put(&measure, &value)) return false;
    size = 4 + measure.pos;
    return true;
}

/** Encode a frame into caller-owned storage disjoint from the value and its borrowed data. */
template<class T>
inline bool encode(const T &value, endian order, uint8_t *data, size_t capacity,
                   size_t &written) UWROSV2_FRANKA_CDR_NOEXCEPT {
    size_t needed;
    if (!data || (order != little_endian && order != big_endian) ||
        !encoded_size(value, needed) || needed > capacity) return false;
    writer w = {data + 4, needed - 4, 0, order};
    if (!value_codec<T>::put(&w, &value)) return false;
    write_header(data, order);
    written = needed;
    return true;
}

/** Commit all decoded fields together. Strings and sequences borrow the immutable frame. */
template<class T>
inline bool decode(const uint8_t *data, size_t size, T &out) UWROSV2_FRANKA_CDR_NOEXCEPT {
    reader r;
    T value;
    if (!begin_read(&r, data, size) || !value_codec<T>::get(&r, &value) || !end_read(&r)) return false;
    out = value;
    return true;
}

template<class T>
inline bool validate(const uint8_t *data, size_t size) UWROSV2_FRANKA_CDR_NOEXCEPT {
    reader r;
    T value;
    return begin_read(&r, data, size) && value_codec<T>::get(&r, &value) && end_read(&r);
}

} } } // namespace uwrosv2::franka::cdr
#endif
