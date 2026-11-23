struct Reading {
    int count;
};

extern "C" int value()
{
    return SDK_GENERATION;
}

static volatile int input = 40;

extern "C" void _start()
{
    Reading sample{input};
    int local = sample.count;
    local += 2;                      /* SOURCE_BREAK */
    if (local != 42)                 /* SOURCE_STEP */
        __builtin_trap();
}

#ifdef SDK_SHARED
extern "C" void wasi_thread_start(int id, int argument)
{
    (void)id;
    (void)argument;
}
#endif
