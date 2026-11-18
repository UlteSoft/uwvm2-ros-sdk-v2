extern "C" void visit_frame(unsigned char *, unsigned char *, unsigned);
extern "C" void cleanup_frame(unsigned char *, unsigned char *);
extern "C" unsigned cleanup_count();

struct Cleanup {
    unsigned char *first;
    unsigned char *second;
    ~Cleanup() { cleanup_frame(first, second); }
};

[[gnu::noinline]] static void throw_from_frame(unsigned round) {
    alignas(16) unsigned char first[16];
    alignas(16) unsigned char second[16];
    visit_frame(first, second, round);
    Cleanup cleanup{first, second};
    throw round + 1U;
}

[[gnu::noinline]] static void rethrow_from_handler(unsigned round) {
    try {
        throw_from_frame(round);
    } catch (unsigned value) {
        if (value != round + 1U || cleanup_count() != round + 1U)
            __builtin_trap();
        throw;
    }
}

extern "C" void _start() {
    for (unsigned round = 0; round < 32; ++round) {
        try {
            rethrow_from_handler(round);
            __builtin_trap();
        } catch (unsigned value) {
            if (value != round + 1U || cleanup_count() != value)
                __builtin_trap();
        }
    }
}
