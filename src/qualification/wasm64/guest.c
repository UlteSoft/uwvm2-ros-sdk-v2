#define _POSIX_C_SOURCE 200809L
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

_Static_assert(sizeof(void *) == 8 && sizeof(size_t) == 8, "expected memory64 C ABI");

int main(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0)
        return 71;

    size_t size = 48 + (now.tv_nsec & 15);
    char *allocation = malloc(size);
    if (allocation == NULL)
        return 72;

    int written = snprintf(allocation, size, "ptr=%zu, value=%.2Lf", sizeof(void *), 1.25L);
    int matched = written == 17 && strcmp(allocation, "ptr=8, value=1.25") == 0;
    free(allocation);
    _Exit(matched ? 42 : 73);
}
