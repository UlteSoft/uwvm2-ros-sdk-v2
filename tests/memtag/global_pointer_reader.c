extern unsigned char *volatile origins[6];

static __UINTPTR_TYPE__ address(unsigned char *p) {
    return (__UINTPTR_TYPE__)__builtin_wasm_memtag_untag(0, p);
}

static unsigned tag(unsigned char *p) {
    return (unsigned)__builtin_wasm_memtag_extract(0, p);
}

void check_pointer_origins(int enabled) {
    unsigned char *a = origins[0], *b = origins[3];
    unsigned char *a_last = origins[1], *b_last = origins[4];
    unsigned char *a_end = origins[2], *b_end = origins[5];
    if (address(a_last) != address(a) + 15 || address(a_end) != address(a) + 16 ||
        address(b_last) != address(b) + 15 || address(b_end) != address(b) + 16)
        __builtin_trap();
    if (address(a_end) != address(b) && address(b_end) != address(a))
        __builtin_trap();
    if (tag(a_last) != tag(a) || tag(a_end) != tag(a) ||
        tag(b_last) != tag(b) || tag(b_end) != tag(b))
        __builtin_trap();
    if (enabled ? (!tag(a) || !tag(b) || tag(a) == tag(b)) : (tag(a) || tag(b)))
        __builtin_trap();
    if (a[0] != 11 || b[0] != 22)
        __builtin_trap();
    *a_last = 71;
    *b_last = 82;
    if (a[15] != 71 || b[15] != 82)
        __builtin_trap();
}
