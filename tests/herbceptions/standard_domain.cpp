#include <herbceptions/error>

[[gnu::noinline]] void fail_parse() throws {
    throw throws std::parse_errc::invalid;
}
#ifdef __cpp_exceptions
struct legacy_failure { int value; };
[[gnu::noinline]] void fail_legacy() { throw legacy_failure{63}; }
[[gnu::noinline]] void convert_legacy() throws { fail_legacy(); }
static void check_legacy() {
    try {
        convert_legacy();
    } catch throws(std::error status) {
        auto* record = std::exception_cast_std_error<const legacy_failure*>(status);
        if (!record || record->value != 63) __builtin_trap();
        auto saved = std::make_exception_ptr_from_std_error(status);
        if (!saved) __builtin_trap();
        try { std::rethrow_exception(saved); }
        catch (const legacy_failure& e) { if (e.value == 63) return; }
    }
    __builtin_trap();
}
#endif
extern "C" void _start() {
#ifdef __cpp_exceptions
    check_legacy();
#endif
    try {
        fail_parse();
    } catch throws(std::error status) {
        if (status.domain() == std::error_domains::__cxa_error_domain_parse()
            && status.code() == static_cast<__SIZE_TYPE__>(std::parse_errc::invalid)
            && status.equivalent(std::parse_errc::invalid)) return;
    }
    __builtin_trap();
}
