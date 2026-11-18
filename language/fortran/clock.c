/** @file clock.c
 * @brief Implement Flang's clock intrinsics with the two matching WASI clock IDs.
 * @details Queries execute with the guest's current clock grants. An unavailable
 * monotonic clock returns the Fortran failure sentinel and zero rate/maximum.
 * Process CPU time uses a separate permission and reports failure as a negative
 * duration. No clock value or authorization result is cached across calls.
 */
#include <stdint.h>
#include <wasi/api.h>

static int64_t count_maximum(int kind) {
    switch (kind) {
        case 1: return INT8_MAX;
        case 2: return INT16_MAX;
        case 4: return INT32_MAX;
        case 8: case 16: return INT64_MAX;
        default: return 0;
    }
}

static uint64_t ticks_per_second(int kind) {
    return kind >= 8 ? UINT64_C(1000000000) : kind >= 2 ? UINT64_C(1000) : UINT64_C(10);
}

static __wasi_errno_t elapsed(__wasi_timestamp_t *timestamp) {
    return __wasi_clock_time_get(__WASI_CLOCKID_MONOTONIC, 1, timestamp);
}

int64_t _FortranASystemClockCount(int kind) {
    const int64_t maximum = count_maximum(kind);
    __wasi_timestamp_t timestamp;
    if (!maximum || elapsed(&timestamp)) return -maximum;
    const uint64_t quantum = UINT64_C(1000000000) / ticks_per_second(kind);
    return (int64_t)((timestamp / quantum) & (uint64_t)maximum);
}

int64_t _FortranASystemClockCountRate(int kind) {
    __wasi_timestamp_t timestamp;
    return count_maximum(kind) && !elapsed(&timestamp) ? (int64_t)ticks_per_second(kind) : 0;
}

int64_t _FortranASystemClockCountMax(int kind) {
    __wasi_timestamp_t timestamp;
    return elapsed(&timestamp) ? 0 : count_maximum(kind);
}

double _FortranACpuTime(void) {
    __wasi_timestamp_t timestamp;
    return __wasi_clock_time_get(__WASI_CLOCKID_PROCESS_CPUTIME_ID, 1, &timestamp)
        ? -1.0 : (double)timestamp / 1.e9;
}
