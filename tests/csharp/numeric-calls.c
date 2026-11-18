#ifdef __wasm__
__attribute__((import_module("component"), import_name("evaluate")))
#endif
extern unsigned evaluate(unsigned);
unsigned check(unsigned n) {
    unsigned result = 0;
    for (unsigned i = 0; i < n; ++i)
        result += evaluate(i);
    unsigned expected = (unsigned)((unsigned long long)n*(n-1)/2)*7 - n*3;
    if (result != expected) __builtin_trap();
    return result;
}
#ifndef __wasm__
#include <stdlib.h>
int main(int argc, char** argv) {
    if (argc != 2) return 2;
    volatile unsigned checked = check((unsigned)strtoul(argv[1], 0, 10));
    (void)checked;
    return 0;
}
#endif
