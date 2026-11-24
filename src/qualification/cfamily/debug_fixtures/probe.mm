template <typename T>
struct Reading {
    T count;
    T get() const { return count; }
};

__attribute__((objc_root_class))
@interface QualificationReading
+ (int)adjust:(int)reading;
@end

@implementation QualificationReading
+ (int)adjust:(int)reading
{
    Reading<int> sample{reading};
    int local = sample.get();
    local += 2;                      /* SOURCE_BREAK */
    if (local != reading + 2)        /* SOURCE_STEP */
        __builtin_trap();
    return local;
}
@end

static volatile int input = 40;

extern "C" int value()
{
    return [QualificationReading adjust:SDK_GENERATION - 2];
}

#ifdef SDK_SHARED
#include <pthread.h>

static void *read_input(void *argument)
{
    *static_cast<int *>(argument) = input;
    return nullptr;
}

int main()
{
    pthread_t worker;
    int reading = 0;
    if (pthread_create(&worker, nullptr, read_input, &reading) || pthread_join(worker, nullptr))
        return 1;
    return [QualificationReading adjust:reading] != 42;
}
#else
extern "C" void _start()
{
    if ([QualificationReading adjust:input] != 42)
        __builtin_trap();
}
#endif
