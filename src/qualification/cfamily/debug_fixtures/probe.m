__attribute__((objc_root_class))
@interface QualificationReading
+ (int)adjust:(int)reading;
@end

@implementation QualificationReading
+ (int)adjust:(int)reading
{
    int local = reading;
    local += 2;                      /* SOURCE_BREAK */
    if (local != reading + 2)        /* SOURCE_STEP */
        __builtin_trap();
    return local;
}
@end

static volatile int input = 40;

int value(void)
{
    return [QualificationReading adjust:SDK_GENERATION - 2];
}

void _start(void)
{
    if ([QualificationReading adjust:input] != 42)
        __builtin_trap();
}

#ifdef SDK_SHARED
void wasi_thread_start(int id, int argument)
{
    (void)id;
    (void)argument;
}
#endif
