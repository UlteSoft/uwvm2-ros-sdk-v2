#define _POSIX_C_SOURCE 200809L
#include "guest.h"
#define main qualification_chromium_client
#include "../../objc/clients/chromium-swizzler.mm"
#undef main

static __attribute__((noinline)) uint64_t dispatch(Class target, SwizzleTarget *object, unsigned count)
{
    uint64_t sum = 0;
    for (unsigned i = 0; i < count; ++i) {
        int value = int(i & 31);
        {
            base::apple::ScopedObjCClassSwizzler swap(target, @selector(score:), @selector(replacement:));
            sum += [object score:value] + swap.InvokeOriginal<int>(object, @selector(score:), value);
        }
        sum += [object score:value];
    }
    return sum;
}

int main()
{
    bench_report_mode();
    if (qualification_chromium_client())
        abort();
    Class target = objc_getClass("SwizzleTarget");
    auto *object = static_cast<SwizzleTarget *>(class_createInstance(target, 0));
    if (!object || dispatch(target, object, 32) != 2928)
        abort();
    const unsigned count = 4096;
    uint64_t start = bench_tick();
    uint64_t sum = dispatch(target, object, count);
    uint64_t end = bench_tick();
    object_dispose(object);
    bench_result("objcpp workload=chromium-swizzler", count, sum, start, end);
    return 0;
}
