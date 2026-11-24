/* Common WASIp1 libc implementations for both address widths. Volatile byte
   accesses avoid recursive libcalls and keep the target's MTE checks intact. */
typedef __SIZE_TYPE__ size_t;
typedef __UINTPTR_TYPE__ uintptr_t;

static inline uintptr_t linear_address(const void *p)
{
#if __has_feature(memtag_heap)
    return (uintptr_t)__builtin_wasm_memtag_untag(0, (void *)p);
#else
    return (uintptr_t)p;
#endif
}

static inline void check_range(const void *p, size_t n)
{
    if (!n)
        return;
    uintptr_t addr = linear_address(p);
    /* Compare the final page, not memory.size * 65536, which wraps for a
       full 4 GiB wasm32 memory. Check addition before forming the last byte. */
    if (n - 1 > (uintptr_t)-1 - addr ||
        ((addr + (n - 1)) >> 16) >= __builtin_wasm_memory_size(0))
        __builtin_trap();
#if __has_feature(memtag_heap)
    /* Match the VM's actual access policy (including its tag comparison
       mask). Check every touched sixteen-byte granule before the first store. */
    const volatile unsigned char *bytes = p;
    size_t offset = 0;
    do {
        (void)bytes[offset];
        size_t step = 16 - ((addr + offset) & 15);
        if (step >= n - offset)
            break;
        offset += step;
    } while (1);
#endif
}

static __attribute__((always_inline)) inline void fill(void *destination, unsigned char value, size_t n)
{
    check_range(destination, n);
    volatile unsigned char *d = destination;
    for (size_t i = 0; i < n; ++i)
        d[i] = value;
}

__attribute__((weak)) void *memset(void *destination, int value, size_t n)
{
    fill(destination, (unsigned char)value, n);
    return destination;
}

/* LLD calls this while it owns the shared-memory initialization flag, before
   publishing the initialized image. The synthetic call has no input relocation.
   Retain the hidden definition when LLD extracts this archive member with -u. */
__attribute__((visibility("hidden"), retain)) void __wros_scalar_zero_bss(void *destination, size_t n)
{
    fill(destination, 0, n);
}

__attribute__((weak)) void *memmove(void *destination, const void *source, size_t n)
{
    check_range(source, n);
    check_range(destination, n);
    uintptr_t dst = linear_address(destination);
    uintptr_t src = linear_address(source);
    volatile unsigned char *d = destination;
    const volatile unsigned char *s = source;
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

__attribute__((weak)) void *memcpy(void *destination, const void *source, size_t n)
{
    check_range(source, n);
    check_range(destination, n);
    volatile unsigned char *d = destination;
    const volatile unsigned char *s = source;
    for (size_t i = 0; i < n; ++i)
        d[i] = s[i];
    return destination;
}
