/** @file Run zlib's Adler-32 implementation inside a guest. */
#include <uwrosv2/scene.h>
#define Z_SOLO
#include "upstream/adler32.c"

void _start(void) {
    static const unsigned char message[] = "Wikipedia";
    if (uwrosv2_abi() != 2 || adler32(1, message, sizeof(message) - 1) != 0x11e60398UL)
        __builtin_trap();
}
