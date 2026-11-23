/** Allocation-free C++98 ROS 1 wire primitives. */
#ifndef UWROSV2_ABB_ROS1_WIRE_HPP
#define UWROSV2_ABB_ROS1_WIRE_HPP
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#ifndef UWROSV2_ABB_ROS1_NOEXCEPT
# if __cplusplus >= 201103L
#  define UWROSV2_ABB_ROS1_NOEXCEPT noexcept
# else
#  define UWROSV2_ABB_ROS1_NOEXCEPT throw()
# endif
#endif

namespace uwrosv2 { namespace abb { namespace ros1 {

/** A borrowed ROS 1 string. Embedded NULs are valid. The bytes need no terminator. */
struct String {
    const uint8_t *data; /**< Readable bytes, optionally null for a zero-byte string. */
    size_t size;         /**< Byte count representable as a ROS uint32. */
};
/** Standard two-word ROS 1 timestamp. */
struct Time {
    uint32_t sec;  /**< Seconds since the ROS time epoch. */
    uint32_t nsec; /**< Nanoseconds within the indicated second. */
};
template<class T> class Sequence;

/** @cond INTERNAL */
namespace detail {
typedef char FloatWidths[(sizeof(float) == 4 && sizeof(double) == 8) ? 1 : -1];

class Reader {
    const uint8_t *data_;
    size_t size_, pos_;
    bool word(size_t width, uint64_t &out) UWROSV2_ABB_ROS1_NOEXCEPT {
        if (width > remaining()) return false;
        uint64_t bits = 0;
        for (size_t i = 0; i < width; ++i) bits |= static_cast<uint64_t>(data_[pos_++]) << (8 * i);
        out = bits;
        return true;
    }
public:
    Reader(const uint8_t *data, size_t size) UWROSV2_ABB_ROS1_NOEXCEPT : data_(data), size_(size), pos_(0) {}
    size_t remaining() const UWROSV2_ABB_ROS1_NOEXCEPT { return size_ - pos_; }
    const uint8_t *current() const UWROSV2_ABB_ROS1_NOEXCEPT { return data_ ? data_ + pos_ : 0; }
    bool field(uint8_t &out) UWROSV2_ABB_ROS1_NOEXCEPT {
        if (!remaining()) return false;
        out = data_[pos_++];
        return true;
    }
    bool field(bool &out) UWROSV2_ABB_ROS1_NOEXCEPT {
        uint8_t b;
        if (!field(b) || b > 1) return false;
        out = b != 0;
        return true;
    }
    bool field(uint16_t &out) UWROSV2_ABB_ROS1_NOEXCEPT {
        uint64_t bits;
        if (!word(2, bits)) return false;
        out = static_cast<uint16_t>(bits);
        return true;
    }
    bool field(uint32_t &out) UWROSV2_ABB_ROS1_NOEXCEPT {
        uint64_t bits;
        if (!word(4, bits)) return false;
        out = static_cast<uint32_t>(bits);
        return true;
    }
    bool field(float &out) UWROSV2_ABB_ROS1_NOEXCEPT {
        uint32_t bits;
        if (!field(bits)) return false;
        memcpy(&out, &bits, sizeof bits);
        return true;
    }
    bool field(double &out) UWROSV2_ABB_ROS1_NOEXCEPT {
        uint64_t bits;
        if (!word(8, bits)) return false;
        memcpy(&out, &bits, sizeof bits);
        return true;
    }
    bool field(String &out) UWROSV2_ABB_ROS1_NOEXCEPT {
        uint32_t length;
        if (!field(length) || length > remaining()) return false;
        out.data = current();
        out.size = length;
        pos_ += length;
        return true;
    }
    bool field(Time &out) UWROSV2_ABB_ROS1_NOEXCEPT { return field(out.sec) && field(out.nsec); }
    template<class T> bool field(T &out) UWROSV2_ABB_ROS1_NOEXCEPT { return T::fields(*this, out); }
    template<class T> bool field(Sequence<T> &out) UWROSV2_ABB_ROS1_NOEXCEPT;
};

class Writer {
    uint8_t *data_;
    size_t capacity_, pos_;
    bool word(size_t width, uint64_t value) UWROSV2_ABB_ROS1_NOEXCEPT {
        if (width > capacity_ - pos_) return false;
        if (data_) {
            for (size_t i = 0; i < width; ++i) data_[pos_ + i] = static_cast<uint8_t>(value >> (8 * i));
        }
        pos_ += width;
        return true;
    }
    bool bytes(const uint8_t *data, size_t size) UWROSV2_ABB_ROS1_NOEXCEPT {
        if (size > capacity_ - pos_ || (size && !data)) return false;
        if (data_ && size) memcpy(data_ + pos_, data, size);
        pos_ += size;
        return true;
    }
public:
    Writer(uint8_t *data, size_t capacity) UWROSV2_ABB_ROS1_NOEXCEPT : data_(data), capacity_(capacity), pos_(0) {}
    size_t size() const UWROSV2_ABB_ROS1_NOEXCEPT { return pos_; }
    bool field(bool value) UWROSV2_ABB_ROS1_NOEXCEPT { return word(1, value ? 1 : 0); }
    bool field(uint8_t value) UWROSV2_ABB_ROS1_NOEXCEPT { return word(1, value); }
    bool field(uint16_t value) UWROSV2_ABB_ROS1_NOEXCEPT { return word(2, value); }
    bool field(uint32_t value) UWROSV2_ABB_ROS1_NOEXCEPT { return word(4, value); }
    bool field(const float &value) UWROSV2_ABB_ROS1_NOEXCEPT {
        uint32_t bits;
        memcpy(&bits, &value, sizeof bits);
        return word(4, bits);
    }
    bool field(const double &value) UWROSV2_ABB_ROS1_NOEXCEPT {
        uint64_t bits;
        memcpy(&bits, &value, sizeof bits);
        return word(8, bits);
    }
    bool field(const String &value) UWROSV2_ABB_ROS1_NOEXCEPT {
        return value.size == static_cast<uint32_t>(value.size) && word(4, value.size) && bytes(value.data, value.size);
    }
    bool field(const Time &value) UWROSV2_ABB_ROS1_NOEXCEPT { return field(value.sec) && field(value.nsec); }
    template<class T> bool field(const T &value) UWROSV2_ABB_ROS1_NOEXCEPT { return T::fields(*this, value); }
    template<class T> bool field(const Sequence<T> &value) UWROSV2_ABB_ROS1_NOEXCEPT;
};
} // namespace detail
/** @endcond */

/** A sequence borrows a caller-owned typed array or an immutable validated message body. */
template<class T> class Sequence {
    const T *values_;
    size_t count_;
    String wire_;
    friend class detail::Reader;
    friend class detail::Writer;
public:
    /** Construct an empty sequence. */
    Sequence() UWROSV2_ABB_ROS1_NOEXCEPT : values_(0), count_(0), wire_() {}
    /** Borrow count contiguous elements for encoding. Their fields must remain readable and immutable. */
    static Sequence from_values(const T *values, size_t count) UWROSV2_ABB_ROS1_NOEXCEPT {
        Sequence result;
        result.values_ = values;
        result.count_ = count;
        return result;
    }
    /** Number of typed elements. */
    size_t size() const UWROSV2_ABB_ROS1_NOEXCEPT { return count_; }
    /** Single-pass cursor over either a typed array or variable-width wire elements. */
    class Iterator {
        const T *values_;
        size_t remaining_;
        detail::Reader reader_;
    public:
        explicit Iterator(const Sequence &seq) UWROSV2_ABB_ROS1_NOEXCEPT
            : values_(seq.values_), remaining_(seq.count_), reader_(seq.wire_.data, seq.wire_.size) {}
        /** Advance the cursor and assign out on success. Returns false at the end. */
        bool next(T &out) UWROSV2_ABB_ROS1_NOEXCEPT {
            if (!remaining_) return false;
            if (values_) out = *values_++;
            else {
                T value;
                if (!reader_.field(value)) return false;
                out = value;
            }
            --remaining_;
            return true;
        }
    };
    /** Start at the first element. Creating another iterator restarts traversal. */
    Iterator iter() const UWROSV2_ABB_ROS1_NOEXCEPT { return Iterator(*this); }
};

/** @cond INTERNAL */
namespace detail {
template<class T> bool Reader::field(Sequence<T> &out) UWROSV2_ABB_ROS1_NOEXCEPT {
    uint32_t count;
    if (!field(count) || count > remaining() / T::minimum_wire_size) return false;
    const size_t start = remaining();
    const uint8_t *data = current();
    T element;
    for (uint32_t i = 0; i < count; ++i) if (!field(element)) return false;
    out.values_ = 0;
    out.count_ = count;
    out.wire_.data = data;
    out.wire_.size = start - remaining();
    return true;
}

template<class T> bool Writer::field(const Sequence<T> &value) UWROSV2_ABB_ROS1_NOEXCEPT {
    if (value.size() != static_cast<uint32_t>(value.size()) || !word(4, value.size())) return false;
    if (!value.values_) {
        if (value.count_ && !value.wire_.data) return false;
        return bytes(value.wire_.data, value.wire_.size);
    }
    if (value.size() > (capacity_ - pos_) / T::minimum_wire_size) return false;
    for (size_t i = 0; i < value.size(); ++i) if (!field(value.values_[i])) return false;
    return true;
}
} // namespace detail
/** @endcond */

/**
 * Measure one ROS 1 body, including its nested strings and record sequences.
 * @param value Typed message or service body with readable source spans.
 * @param out Receives the exact byte count on success.
 * @return True on success. An invalid span or length exceeding a ROS uint32 leaves out untouched.
 */
template<class T> bool encoded_size(const T &value, size_t &out) UWROSV2_ABB_ROS1_NOEXCEPT {
    detail::Writer measure(0, UINT32_MAX);
    if (!measure.field(value)) return false;
    out = measure.size();
    return true;
}
/**
 * Serialize a complete ROS 1 message, request or response body in little-endian field order.
 * @param value Input record. Keep its borrowed storage immutable throughout the operation.
 * @param out Destination disjoint from the input record and referenced spans. An empty body permits null.
 * @param capacity Available destination bytes.
 * @param written Disjoint byte-count slot assigned on success.
 * @return True on success. An invalid source or insufficient capacity preserves the buffer and count.
 */
template<class T> bool encode(const T &value, uint8_t *out, size_t capacity,
                              size_t &written) UWROSV2_ABB_ROS1_NOEXCEPT {
    size_t size;
    if (!encoded_size(value, size) || size > capacity || (size && !out)) return false;
    detail::Writer writer(out, capacity);
    if (!writer.field(value)) return false;
    written = size;
    return true;
}
/**
 * Decode one complete ROS 1 body. Strings and sequences borrow bytes from data.
 * @param data Readable immutable payload. An empty message permits a null pointer.
 * @param size Exact payload byte count.
 * @param out Typed result. Keep data alive and immutable while using its borrowed fields.
 * @return True on success. Invalid lengths, booleans, truncation or trailing bytes preserve out.
 */
template<class T> bool decode(const uint8_t *data, size_t size, T &out) UWROSV2_ABB_ROS1_NOEXCEPT {
    if ((size && !data) || size != static_cast<uint32_t>(size)) return false;
    detail::Reader reader(data, size);
    T value;
    if (!reader.field(value) || reader.remaining()) return false;
    out = value;
    return true;
}
/**
 * Validate the complete body, including every nested string and sequence element.
 * @param data Readable immutable payload.
 * @param size Exact payload length in bytes.
 * @return True when the bytes form a complete canonical body of T.
 */
template<class T> bool validate(const uint8_t *data, size_t size) UWROSV2_ABB_ROS1_NOEXCEPT {
    T value;
    return decode(data, size, value);
}
} } } // namespace uwrosv2::abb::ros1
#endif
