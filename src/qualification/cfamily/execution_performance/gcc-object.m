#define _POSIX_C_SOURCE 200809L
#include "guest.h"
#define main qualification_gcc_client
#include "../../objc/clients/gcc-object.m"
#undef main

static __attribute__((noinline)) uint64_t dispatch(QualificationGCCObject *first,
                                                   QualificationGCCObject *second, Class child, unsigned count)
{
    uint64_t sum = 0;
    for (unsigned i = 0; i < count; ++i) {
        QualificationGCCObject *object = (i & 1) ? second : first;
        sum += ([object class] == child ? 4u : 0u) + ([object isEqual:first] ? 2u : 0u)
             + ([object isEqual:second] ? 1u : 0u);
    }
    return sum;
}

int main(void)
{
    bench_report_mode();
    if (qualification_gcc_client())
        abort();
    Class root = objc_getClass("QualificationGCCObject"), child = objc_getClass("GCCChild");
    QualificationGCCObject *first = class_createInstance(root, 0), *second = class_createInstance(child, 0);
    if (!first || !second || dispatch(first, second, child, 256) != 128 * 7)
        abort();
    const unsigned count = 65536;
    uint64_t start = bench_tick();
    uint64_t sum = dispatch(first, second, child, count);
    uint64_t end = bench_tick();
    object_dispose(second);
    object_dispose(first);
    bench_result("objc workload=gcc-object", count, sum, start, end);
    return 0;
}
