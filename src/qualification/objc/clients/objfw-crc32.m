#import "OFCRC32.h"
#include <stdio.h>

int main(void)
{
    const char text[] = "123456789";
    const unsigned char binary[] = {0, 1, 2, 3, 0x7f, 0x80, 0xfe, 0xff};
    const uint32_t initial = UINT32_MAX;
    uint32_t split = _OFCRC32(initial, text, 4);
    split = _OFCRC32(split, text + 4, 5);
    if ((_OFCRC32(initial, text, 9) ^ initial) != UINT32_C(0xcbf43926) ||
        (split ^ initial) != UINT32_C(0xcbf43926) || _OFCRC32(split, text, 0) != split)
        return 1;
    if ((_OFCRC32(initial, binary, sizeof binary) ^ initial) != UINT32_C(0xbc6987f2))
        return 2;
    puts("objfw-crc32-ok");
    return 0;
}
