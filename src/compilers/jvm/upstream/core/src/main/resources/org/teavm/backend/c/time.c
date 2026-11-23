#include "time.h"
#include <stdint.h>
#include <wasi/api.h>

void teavm_initTime(void) {}

static uint64_t read_clock(__wasi_clockid_t clock) {
    __wasi_timestamp_t ns = 0;
    if (__wasi_clock_time_get(clock, 1, &ns)) __builtin_trap();
    return ns;
}
int64_t teavm_currentTimeMillis(void) { return (int64_t)(read_clock(__WASI_CLOCKID_REALTIME)/UINT64_C(1000000)); }
int64_t teavm_currentTimeNano(void) { return (int64_t)read_clock(__WASI_CLOCKID_MONOTONIC); }
int32_t teavm_timeZoneOffset(void) { return 0; }
