#ifndef WROS_PHP_UCONTEXT_H
#define WROS_PHP_UCONTEXT_H
#include <stddef.h>

typedef struct wros_php_context {
    struct { void *ss_sp; size_t ss_size; int ss_flags; } uc_stack;
    struct wros_php_context *uc_link;
} ucontext_t;

int getcontext(ucontext_t *);
void makecontext(ucontext_t *, void (*)(void), int, ...);
int swapcontext(ucontext_t *, const ucontext_t *);

#endif
