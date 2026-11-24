#include "tag_access.h"
#include <unistd.h>

/* The separately compiled check_word receives a live, escaping stack object. */
void check_access(unsigned mode, unsigned delta) {
    unsigned char storage[48] __attribute__((aligned(16))) = {0};
    check_word(storage, mode, delta);
}

/* These fixed-size copies are valid at byte alignment in all four dialects. */
__attribute__((noinline)) uint32_t read_word(const unsigned char *p) {
    uint32_t value;
    __builtin_memcpy(&value, p, sizeof value);
    return value;
}

__attribute__((noinline)) void write_word(unsigned char *p, uint32_t value) {
    __builtin_memcpy(p, &value, sizeof value);
}

void observe(unsigned mode, unsigned delta, uintptr_t address, unsigned logical,
             unsigned first, unsigned last) {
    const uint64_t record[] = {mode, delta, address, logical, first, last};
    if (write(1, record, sizeof record) != (ssize_t)sizeof record)
        __builtin_trap();
}

void completed(uint32_t value) {
    if (write(1, &value, sizeof value) != (ssize_t)sizeof value)
        __builtin_trap();
}

int main(int argc, char **argv) {
    if (argc != 3 || argv[1][0] < '0' || argv[1][0] > '5' || argv[1][1] || !argv[2][0])
        return 2;
    unsigned mode = (unsigned)(argv[1][0] - '0'), delta = 0;
    for (const char *p = argv[2]; *p; ++p) {
        if (*p < '0' || *p > '9' || (delta = delta * 10 + (unsigned)(*p - '0')) > 255)
            return 2;
    }
    if (mode < 4) {
        check_access(mode, delta);
        return 0;
    }
#if TEST_MTE
    if (delta == 0) {
        check_lifecycle(mode);
        return 0;
    }
#endif
    return 2;
}
