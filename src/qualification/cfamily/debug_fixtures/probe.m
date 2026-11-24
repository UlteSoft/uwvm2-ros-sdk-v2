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

#ifdef SDK_SHARED
#include <pthread.h>

static void *read_input(void *argument)
{
    *(int *)argument = input;
    return NULL;
}

int main(void)
{
    pthread_t worker;
    int reading = 0;
    if (pthread_create(&worker, NULL, read_input, &reading) || pthread_join(worker, NULL))
        return 1;
    return [QualificationReading adjust:reading] != 42;
}
#else
void _start(void)
{
    if ([QualificationReading adjust:input] != 42)
        __builtin_trap();
}
#endif
