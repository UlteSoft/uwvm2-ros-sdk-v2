/* The two builds change only the body of the approved business export. */
int value(void)
{
    return SDK_GENERATION;
}

static volatile int input = 40;

void _start(void)
{
    int local = input;
    local += 2;                      /* SOURCE_BREAK */
    if (local != 42)                 /* SOURCE_STEP */
        __builtin_trap();
}

#ifdef SDK_SHARED
void wasi_thread_start(int id, int argument)
{
    (void)id;
    (void)argument;
}
#endif
