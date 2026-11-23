/** @file Independent freestanding C++ guest values and bounded byte views. */
#pragma once
#include <stddef.h>
#include <stdint.h>

#if defined(__wasm__)
# define UWROSV2_CPP_IMPORT(name) __attribute__((import_module("uwvm_ros_v2"), import_name(name)))
#else
# define UWROSV2_CPP_IMPORT(name)
#endif
#if __cplusplus >= 201103L
# define UWROSV2_CPP_NOEXCEPT noexcept
# define UWROSV2_CPP_CONSTEXPR constexpr
#else
# define UWROSV2_CPP_NOEXCEPT throw()
# define UWROSV2_CPP_CONSTEXPR
#endif
#if __cplusplus >= 201402L
# define UWROSV2_CPP_CONSTEXPR14 constexpr
# define UWROSV2_CPP_ZERO = 0
#else
# define UWROSV2_CPP_CONSTEXPR14
# define UWROSV2_CPP_ZERO
#endif
#if __cplusplus >= 201703L
# define UWROSV2_CPP_NODISCARD [[nodiscard]]
#else
# define UWROSV2_CPP_NODISCARD
#endif

namespace uwrosv2 {
struct input {
    const uint8_t* data;
    size_t size;
    UWROSV2_CPP_CONSTEXPR input() UWROSV2_CPP_NOEXCEPT : data(0), size(0) {}
    UWROSV2_CPP_CONSTEXPR input(const uint8_t* p, size_t n) UWROSV2_CPP_NOEXCEPT : data(p), size(n) {}
    template<size_t N> UWROSV2_CPP_CONSTEXPR input(const uint8_t (&a)[N]) UWROSV2_CPP_NOEXCEPT : data(a), size(N) {}
};
struct output {
    uint8_t* data;
    size_t size;
    UWROSV2_CPP_CONSTEXPR output() UWROSV2_CPP_NOEXCEPT : data(0), size(0) {}
    UWROSV2_CPP_CONSTEXPR output(uint8_t* p, size_t n) UWROSV2_CPP_NOEXCEPT : data(p), size(n) {}
    template<size_t N> UWROSV2_CPP_CONSTEXPR output(uint8_t (&a)[N]) UWROSV2_CPP_NOEXCEPT : data(a), size(N) {}
};
struct text_view {
    const char* data;
    size_t size;
    UWROSV2_CPP_CONSTEXPR text_view(const char* p, size_t n) UWROSV2_CPP_NOEXCEPT : data(p), size(n) {}
    template<size_t N> UWROSV2_CPP_CONSTEXPR text_view(const char (&s)[N]) UWROSV2_CPP_NOEXCEPT : data(s), size(N - 1) {}
};
/** Borrowed VM identities. Only their issuing guest may use them. */
struct capability_handle { uint64_t id UWROSV2_CPP_ZERO; };
struct resource_handle { uint64_t id UWROSV2_CPP_ZERO; };
/** size carries a delivered or required extent, including the supported=false
 *  permission page that can accompany unsupported. */
struct transfer {
    uint32_t status UWROSV2_CPP_ZERO;
    uint64_t size UWROSV2_CPP_ZERO;
#if __cplusplus >= 201103L
    constexpr explicit operator bool() const noexcept { return status == 0; }
#else
private:
    typedef uint32_t transfer::*bool_type;
public:
    operator bool_type() const throw() { return status == 0 ? &transfer::status : 0; }
#endif
};
template<class T> struct result {
    transfer call;
    T value;
#if __cplusplus >= 201103L
    constexpr explicit operator bool() const noexcept { return static_cast<bool>(call); }
#else
private:
    typedef transfer result::*bool_type;
public:
    operator bool_type() const throw() { return call ? &result::call : 0; }
#endif
};
#undef UWROSV2_CPP_ZERO

namespace detail {
inline uint64_t address(const void* p) UWROSV2_CPP_NOEXCEPT {
    return static_cast<uint64_t>(reinterpret_cast<uintptr_t>(p));
}
inline UWROSV2_CPP_CONSTEXPR14 uint64_t read_word(const uint8_t* p) UWROSV2_CPP_NOEXCEPT {
    uint64_t value = 0;
    for (unsigned i = 0; i != 8; ++i) value |= static_cast<uint64_t>(p[i]) << (8 * i);
    return value;
}
inline UWROSV2_CPP_CONSTEXPR14 void write_word(uint8_t* p, uint64_t value) UWROSV2_CPP_NOEXCEPT {
    for (unsigned i = 0; i != 8; ++i) p[i] = static_cast<uint8_t>(value >> (8 * i));
}
inline UWROSV2_CPP_CONSTEXPR int64_t signed_word(uint64_t value) UWROSV2_CPP_NOEXCEPT {
    return value >> 63 ? -1 - static_cast<int64_t>(~value) : static_cast<int64_t>(value);
}
inline UWROSV2_CPP_CONSTEXPR14 transfer finish(uint32_t code, uint64_t bytes, size_t capacity) UWROSV2_CPP_NOEXCEPT {
    const transfer reply = {code == 0 && bytes > capacity ? 22u : code, bytes};
    return reply;
}
template<class T> inline result<T> with_value(transfer call, const T& value) UWROSV2_CPP_NOEXCEPT {
    const result<T> reply = {call, value};
    return reply;
}
template<class T> inline result<T> failure(uint32_t status, uint64_t size = 0) UWROSV2_CPP_NOEXCEPT {
    const transfer call = {status, size};
    return with_value(call, T());
}
}
}
