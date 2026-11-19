#ifdef __HERBCEPTIONS__
#error "conventional C++ build unexpectedly enabled Herbceptions"
#endif

static_assert(__is_identifier(__is_herbceptions_throws_invocable));
static_assert(__is_identifier(__invoke_herbceptions_return_failure_t));

#if defined(FIXTURE_EXPECT_EH) != defined(__cpp_exceptions)
#error "unexpected conventional C++ exception mode"
#endif
namespace {
[[gnu::noinline]] int read(int value) {
    if (value == 0) {
#ifdef __cpp_exceptions
        throw 19;
#else
        return 19;
#endif
    }
    return value;
}
}
extern "C" void _start() {
    volatile int input = 0;
#ifdef __cpp_exceptions
    try { read(input); }
    catch (int value) { if (value == 19) return; }
#else
    if (read(input) == 19) return;
#endif
    __builtin_trap();
}
