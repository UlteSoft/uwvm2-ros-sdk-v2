#pragma once
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>  // Older velocity_iterator.h relies on this GoogleTest transitive include.

// This adapter runs unchanged upstream TEST bodies in an import-free guest.
// A failed expectation traps immediately. The native GoogleTest oracle runs
// every original case with upstream registration and reporting.
namespace wros_test {
inline volatile std::uint64_t count{};
inline volatile std::uint64_t trace{14695981039346656037ull};
constexpr std::uint64_t predicate(const char* text) {
    std::uint64_t hash = 14695981039346656037ull;
    while (*text) hash = (hash ^ static_cast<unsigned char>(*text++)) * 1099511628211ull;
    return hash;
}
inline void check(bool pass, std::uint64_t id) {
    count = count + 1;
    trace = (trace ^ id) * 1099511628211ull;
    if (!pass) __builtin_trap();
}
template<class Float, class UInt> inline bool equal_ulps(Float left, Float right) {
    if (std::isnan(left) || std::isnan(right)) return false;
    constexpr UInt sign = UInt{1} << (sizeof(UInt) * 8 - 1);
    auto rank = [&](Float value) {
        UInt bits{};
        std::memcpy(&bits, &value, sizeof(bits));
        return (bits & sign) ? UInt(~bits + 1) : UInt(sign | bits);
    };
    UInt a = rank(left), b = rank(right);
    return (a >= b ? a - b : b - a) <= 4;
}
}
namespace testing { inline void InitGoogleTest(int*, char**) {} }
int wros_run_all();
#define RUN_ALL_TESTS() ::wros_run_all()
#define TEST(suite, name) extern "C" __attribute__((noinline)) void wros_test_##suite##_##name()
#define EXPECT_TRUE(...) ::wros_test::check(static_cast<bool>((__VA_ARGS__)), ::wros_test::predicate("true:" #__VA_ARGS__))
#define ASSERT_TRUE(...) EXPECT_TRUE(__VA_ARGS__)
#define EXPECT_FALSE(...) ::wros_test::check(!(__VA_ARGS__), ::wros_test::predicate("false:" #__VA_ARGS__))
#define EXPECT_EQ(a,b) ::wros_test::check((a) == (b), ::wros_test::predicate("eq:" #a "," #b))
#define EXPECT_NE(a,b) ::wros_test::check((a) != (b), ::wros_test::predicate("ne:" #a "," #b))
#define EXPECT_NEAR(a,b,e) ::wros_test::check(std::fabs(double(a) - double(b)) <= double(e), ::wros_test::predicate("near:" #a "," #b "," #e))
#define EXPECT_FLOAT_EQ(a,b) ::wros_test::check(::wros_test::equal_ulps<float, std::uint32_t>((a),(b)), ::wros_test::predicate("float:" #a "," #b))
#define EXPECT_DOUBLE_EQ(a,b) ::wros_test::check(::wros_test::equal_ulps<double, std::uint64_t>((a),(b)), ::wros_test::predicate("double:" #a "," #b))
