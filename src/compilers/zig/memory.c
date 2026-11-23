/* Freestanding fallback for LLVM memory intrinsics on targets without bulk memory. */
typedef __SIZE_TYPE__ size_t;
typedef __UINTPTR_TYPE__ uintptr_t;

void *memcpy(void *destination, const void *source, size_t length) {
    unsigned char *out = destination;
    const unsigned char *in = source;
    for (size_t i = 0; i < length; ++i) out[i] = in[i];
    return destination;
}

void *memmove(void *destination, const void *source, size_t length) {
    unsigned char *out = destination;
    const unsigned char *in = source;
    if ((uintptr_t)out <= (uintptr_t)in) return memcpy(out, in, length);
    while (length != 0) {
        --length;
        out[length] = in[length];
    }
    return destination;
}

void *memset(void *destination, int value, size_t length) {
    unsigned char *out = destination;
    for (size_t i = 0; i < length; ++i) out[i] = (unsigned char)value;
    return destination;
}
