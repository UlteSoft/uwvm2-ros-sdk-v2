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

extern "C" void _start()
{
    if ([QualificationReading adjust:input] != 42)
        __builtin_trap();
}

#ifdef SDK_SHARED
extern "C" void wasi_thread_start(int id, int argument)
{
    (void)id;
    (void)argument;
}
#endif
