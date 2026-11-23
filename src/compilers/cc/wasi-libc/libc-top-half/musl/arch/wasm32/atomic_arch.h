#define a_cas(p, t, s) (__sync_val_compare_and_swap((p), (t), (s)))
#define a_crash() (__builtin_trap())
#define a_clz_32 __builtin_clz
#define a_clz_64 __builtin_clzll
#define a_ctz_32 __builtin_ctz
#define a_ctz_64 __builtin_ctzll

/* Uwvm Preview 1 memory64: pointer CAS must preserve all address/tag bits. */
#ifdef __wasm64__
#if defined(_REENTRANT) && (!defined(__wasip1__) || !defined(__wasm_atomics__) || !defined(__wasm_bulk_memory__))
#error UWVM memory64 threads require WASIp1 with atomics and bulk memory.
#endif
#define a_cas_p a_cas_p
static inline void *a_cas_p(volatile void *p, void *expected, void *desired)
{
    return __sync_val_compare_and_swap((void *volatile *)p, expected, desired);
}
#endif
