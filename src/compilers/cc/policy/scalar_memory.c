/* Guest libc fallbacks for -mno-bulk-memory-opt. Volatile byte access keeps
   Clang from recognizing these implementations as calls to themselves. */
typedef __SIZE_TYPE__ size_t;
typedef __UINTPTR_TYPE__ uintptr_t;

static inline uintptr_t linear_address(const void *pointer)
{
#if __has_feature(memtag_heap)
    /* Only the physical address determines overlap. Keep the original tagged
       pointers for every load and store so normal MTE checks still apply. */
    return (uintptr_t)__builtin_wasm_memtag_untag(0, (void *)pointer);
#else
    return (uintptr_t)pointer;
#endif
}

__attribute__((weak)) void *memcpy(void *destination, const void *source, size_t n)
{
    volatile unsigned char *d = destination;
    const volatile unsigned char *s = source;
    for (size_t i = 0; i < n; ++i)
        d[i] = s[i];
    return destination;
}

__attribute__((weak)) void *memmove(void *destination, const void *source, size_t n)
{
    volatile unsigned char *d = destination;
    const volatile unsigned char *s = source;
    if (!n || destination == source)
        return destination;
    uintptr_t dst = linear_address(destination);
    uintptr_t src = linear_address(source);
    if (dst > src && dst - src < n) {
        while (n != 0) {
            --n;
            d[n] = s[n];
        }
    } else {
        for (size_t i = 0; i < n; ++i)
            d[i] = s[i];
    }
    return destination;
}

__attribute__((weak)) void *memset(void *destination, int value, size_t n)
{
    volatile unsigned char *d = destination;
    for (size_t i = 0; i < n; ++i)
        d[i] = (unsigned char)value;
    return destination;
}
