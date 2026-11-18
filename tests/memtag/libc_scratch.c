#define _GNU_SOURCE
#include <sys/select.h>
#include <poll.h>
#include <errno.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <wasi/api.h>
static int tracking, fail_at, allocation_calls, live, bad_fd;
static size_t expected_subscriptions;
static void check(int value) { if (!value) __builtin_trap(); }
void *__real_malloc(size_t);
void __real_free(void *);
void *__wrap_malloc(size_t bytes) {
    if (tracking && ++allocation_calls == fail_at) {
        errno = ENOMEM;
        return NULL;
    }
    void *p = __real_malloc(bytes);
    if (tracking && p) ++live;
    return p;
}
void __wrap_free(void *p) {
    if (tracking && p) { check(live > 0); --live; }
    __real_free(p);
}
__wasi_errno_t __wrap___wasi_poll_oneoff(const __wasi_subscription_t *in, __wasi_event_t *out, __wasi_size_t count, __wasi_size_t *written) {
    check(count == expected_subscriptions);
    if (count == 0) return __WASI_ERRNO_INVAL;
    for (size_t i=0; i<count; ++i) {
        out[i] = (__wasi_event_t){.userdata=in[i].userdata, .type=in[i].u.tag};
        if (bad_fd && in[i].u.tag == __WASI_EVENTTYPE_FD_READ)
            out[i].error = __WASI_ERRNO_BADF;
    }
    *written = count;
    return 0;
}
static void selects(int n, int fail, int bad) {
    fd_set reads;
    fd_set writes;
    FD_ZERO(&reads); FD_ZERO(&writes);
    for (int i=0; i<n; ++i) {
        FD_SET(i, &reads);
        if (!(i%2)) FD_SET(i,&writes);
    }
    bad_fd = bad;
    expected_subscriptions = n + (n+1)/2;
    allocation_calls = live = errno = 0;
    fail_at = fail;
    tracking = 1;
    int result = pselect(n, &reads, &writes, NULL, NULL, NULL);
    tracking = 0;
    check(live == 0);
    if (fail) {
        check(result == -1 && errno == ENOMEM && allocation_calls == fail);
    } else if (bad || !n) {
        check(result == -1 && errno == (bad ? EBADF : ENOTSUP));
    } else {
        check(result == (int)expected_subscriptions);
        for (int i=0; i<n; ++i) {
            check(FD_ISSET(i,&reads));
            check(!!FD_ISSET(i,&writes) == !(i%2));
        }
    }
}
void _start(void) {
    selects(0,0,0);
    selects(2,0,0);
    selects(21,0,0);
    selects(21,0,1);
    for (int fail=1; fail<=3; ++fail) selects(21,fail,0);
    char text[96];
    volatile long double long_value = 1.0L + 0x1p-80L;
    check(snprintf(text,sizeof text,"%.28Lf",long_value) == 30);
    check(strcmp(text,"1.0000000000000000000000008272") == 0);
    check(snprintf(text,sizeof text,"%.2f",1.375) == 4 && strcmp(text,"1.38")==0);
    check(snprintf(text,sizeof text,"%.2Le",0x1p+1000L) == 9 && strcmp(text,"1.07e+301")==0);
}
