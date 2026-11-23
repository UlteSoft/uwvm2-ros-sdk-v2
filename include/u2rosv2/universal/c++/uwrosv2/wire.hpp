/** @file Little-endian bounded record I/O. All backing storage belongs to the caller. */
#pragma once
#include "base.hpp"

namespace uwrosv2 { namespace wire {
class writer {
    output storage_;
    size_t used_;
    uint32_t status_;
    bool room(size_t n) UWROSV2_CPP_NOEXCEPT {
        if (status_) return false;
        if (n <= storage_.size - used_) return true;
        status_ = 90;
        return false;
    }
public:
    explicit writer(output storage) UWROSV2_CPP_NOEXCEPT
        : storage_(storage), used_(0), status_(storage.size && !storage.data ? 22 : 0) {}
    uint32_t status() const UWROSV2_CPP_NOEXCEPT { return status_; }
    input written() const UWROSV2_CPP_NOEXCEPT { return input(storage_.data, status_ ? 0 : used_); }
    void reject() UWROSV2_CPP_NOEXCEPT { if (!status_) status_ = 22; }
    void word(uint64_t value) UWROSV2_CPP_NOEXCEPT {
        if (room(8)) { detail::write_word(storage_.data + used_, value); used_ += 8; }
    }
    /** Copy an already encoded field or raw payload, disjoint from the scratch space. */
    void raw(input bytes) UWROSV2_CPP_NOEXCEPT {
        if (bytes.size && !bytes.data) { reject(); return; }
        if (!room(bytes.size)) return;
        for (size_t i = 0; i < bytes.size; ++i) storage_.data[used_ + i] = bytes.data[i];
        used_ += bytes.size;
    }
    void blob(input bytes) UWROSV2_CPP_NOEXCEPT {
        if (bytes.size > static_cast<size_t>(-1) - 8 || (bytes.size && !bytes.data)) { reject(); return; }
        if (room(8 + bytes.size)) { word(bytes.size); raw(bytes); }
    }
    /** Supply UTF-8. Each VM decoder applies the field's own name or text constraints. */
    void text(text_view value) UWROSV2_CPP_NOEXCEPT {
        blob(input(reinterpret_cast<const uint8_t*>(value.data), value.size));
    }
};

class reader {
    input storage_;
    size_t pos_;
    bool good_;
public:
    explicit reader(input bytes) UWROSV2_CPP_NOEXCEPT : storage_(bytes), pos_(0), good_(bytes.data || !bytes.size) {}
    bool done() const UWROSV2_CPP_NOEXCEPT { return good_ && pos_ == storage_.size; }
    bool word(uint64_t& value) UWROSV2_CPP_NOEXCEPT {
        if (!good_ || storage_.size - pos_ < 8) { good_ = false; return false; }
        value = detail::read_word(storage_.data + pos_);
        pos_ += 8;
        return true;
    }
    bool blob(input& bytes) UWROSV2_CPP_NOEXCEPT {
        uint64_t n = 0;
        if (!word(n) || n > storage_.size - pos_) { good_ = false; return false; }
        bytes = input(storage_.data + pos_, static_cast<size_t>(n));
        pos_ += static_cast<size_t>(n);
        return true;
    }
};
} }
