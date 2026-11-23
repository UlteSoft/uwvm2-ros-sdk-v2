// The syntax and POSIX domain check use the compiler's herbceptions-throws.cpp
// and libherbceptions release_test.cpp fixtures.
#include <cerrno>
#include <herbceptions/error>
#include <type_traits>

#ifndef EXPECT_PTR
#error "the test must specify the guest pointer ABI"
#endif

static_assert(sizeof(void *) * 8 == EXPECT_PTR);
static_assert(sizeof(std::cxx_std_error) == 2 * sizeof(void *));

static volatile unsigned destruction_order;
struct scope_guard {
    const unsigned number;
    [[gnu::noinline]] ~scope_guard() {
        destruction_order = destruction_order * 10 + number;
    }
};

[[gnu::noinline]] static int leaf(int value) throws {
    scope_guard guard{1};
    if (value < 0)
        throw throws std::errc::permission_denied;
    return value + 1;
}

[[gnu::noinline]] static int relay(int value) throws {
    scope_guard guard{2};
    return try(leaf(value)) + 1;
}

int main() {
    volatile int success = 40;
    volatile int failure = -1;
    try {
        if (relay(success) != 42 || destruction_order != 12)
            return 10;
    } catch throws(std::error) {
        return 11;
    }

    destruction_order = 0;
    try {
        relay(failure);
        return 12;
    } catch throws(std::error error) {
        if (destruction_order != 12)
            return 13;
        if (error.domain() != std::error_domains::__cxa_error_domain_posix() ||
            error.code() != EACCES || !(error == std::errc::permission_denied))
            return 14;
    }

    return 42;
}
