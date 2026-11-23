/** @file Shared guest-memory values for the uwvm_ros_v2 C interface. */
#ifndef UWROSV2_C_BASE_H
#define UWROSV2_C_BASE_H
#include <stddef.h>
#include <stdint.h>

#if defined(__wasm__)
# define UWROSV2_C_IMPORT(name) __attribute__((import_module("uwvm_ros_v2"), import_name(name)))
#else
# define UWROSV2_C_IMPORT(name)
#endif
#ifdef __cplusplus
# define UWROSV2_C_LINK extern "C"
# if __cplusplus >= 201103L
#  define UWROSV2_C_NOEXCEPT noexcept
# else
#  define UWROSV2_C_NOEXCEPT throw()
# endif
#else
# define UWROSV2_C_LINK extern
# define UWROSV2_C_NOEXCEPT
#endif

/** A caller-bound capability. Close it with uwrosv2_capability_close. */
typedef struct { uint64_t id; } uwrosv2_capability;
/** An owned resource identity used together with its separately granted capability. */
typedef struct { uint64_t id; } uwrosv2_resource;
typedef struct { const uint8_t *data; size_t size; } uwrosv2_input;
typedef struct { uint8_t *data; size_t size; } uwrosv2_output;
typedef struct { const char *data; size_t size; } uwrosv2_text;
/** status is the carrier status. size is the host's delivered or reported length.
 *  A short buffer can report a size larger than the supplied capacity. Inspect
 *  the status before reading output. A permission report can return a page
 *  even when the observed family reports unsupported. */
typedef struct { uint32_t status; uint64_t size; } uwrosv2_transfer;

static inline uint64_t uwrosv2_address(const void *p) UWROSV2_C_NOEXCEPT { return (uint64_t)(uintptr_t)p; }
static inline uwrosv2_transfer uwrosv2_transfer_result(uint32_t code, uint64_t size, size_t capacity) UWROSV2_C_NOEXCEPT {
    uwrosv2_transfer result = {code == 0 && size > capacity ? 22u : code, size};
    return result;
}
static inline uint64_t uwrosv2_read_le64(const uint8_t *p) UWROSV2_C_NOEXCEPT {
    uint64_t word = 0;
    for (unsigned i = 0; i != 8; ++i) word |= (uint64_t)p[i] << (8 * i);
    return word;
}
static inline void uwrosv2_write_le64(uint8_t *p, uint64_t value) UWROSV2_C_NOEXCEPT {
    for (unsigned i = 0; i != 8; ++i) p[i] = (uint8_t)(value >> (8 * i));
}
static inline int64_t uwrosv2_signed_word(uint64_t value) UWROSV2_C_NOEXCEPT {
    return value >> 63 ? -1 - (int64_t)~value : (int64_t)value;
}
static inline uwrosv2_input uwrosv2_bytes(const void *data, size_t size) UWROSV2_C_NOEXCEPT {
    uwrosv2_input result = {(const uint8_t *)data, size}; return result;
}
static inline uwrosv2_output uwrosv2_mut_bytes(void *data, size_t size) UWROSV2_C_NOEXCEPT {
    uwrosv2_output result = {(uint8_t *)data, size}; return result;
}
static inline uwrosv2_text uwrosv2_string(const char *data, size_t size) UWROSV2_C_NOEXCEPT {
    uwrosv2_text result = {data, size}; return result;
}
#endif
