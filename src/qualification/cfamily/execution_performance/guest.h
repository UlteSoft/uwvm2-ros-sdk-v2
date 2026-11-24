/* Common output protocol for the execution matrix. All reporting is outside the timer. */
#ifndef QUALIFICATION_EXECUTION_GUEST_H
#define QUALIFICATION_EXECUTION_GUEST_H
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static inline uint64_t bench_tick(void)
{
    struct timespec ts;
    __atomic_signal_fence(__ATOMIC_SEQ_CST);
    if (clock_gettime(CLOCK_MONOTONIC, &ts))
        abort();
    __atomic_signal_fence(__ATOMIC_SEQ_CST);
    return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
}

static inline void bench_report_mode(void)
{
    uint32_t tag = 0;
#ifdef EXECUTION_TAGGED
    static volatile uint32_t witness[4] __attribute__((aligned(16)));
    if (__builtin_wasm_memtag_status(0)) {
        void *pointer = (void *)witness;
        tag = __builtin_wasm_memtag_extract(0, pointer);
        void *address = __builtin_wasm_memtag_untag(0, pointer);
        if (!tag || tag != __builtin_wasm_memtag_extract(0, __builtin_wasm_memtag_load(0, address)))
            abort();
    }
#endif
    printf("mte=%" PRIu32 "\n", tag);
}

static inline void bench_result(const char *name, uint64_t items, uint64_t checksum, uint64_t start, uint64_t end)
{
    if (end <= start)
        abort();
    printf("%s items=%" PRIu64 " checksum=%016" PRIx64 " ns=%" PRIu64 "\n", name, items, checksum, end - start);
}
#endif
