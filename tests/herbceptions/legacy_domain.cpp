#include <cstddef>
#include <cxxabi.h>
#include <typeinfo>

// C++ ABI declarations permit testing the domain independently of the syntax frontend.
extern "C" const void* __cxa_error_domain_itanium_exception_ptr() noexcept;
extern "C" void* __cxa_error_code_itanium_exception_ptr_cast(
    const void*, std::size_t, const void*) noexcept;

struct left { virtual ~left() = default; int pad{63}; };
struct reading { virtual ~reading() = default; int code{47}; };
struct device_error final : left, reading {};

extern "C" void _start() {
    const auto* domain = __cxa_error_domain_itanium_exception_ptr();
    if (!domain || __cxa_error_code_itanium_exception_ptr_cast(domain, 0, &typeid(reading)))
        __builtin_trap();
#if defined(__cpp_exceptions)
    void* owned{};
    try { throw device_error{}; }
    catch (...) { owned = __cxxabiv1::__cxa_current_primary_exception(); }
    if (!owned) __builtin_trap();
    const auto bits = reinterpret_cast<std::size_t>(owned);
    const auto* result = static_cast<const reading*>(
        __cxa_error_code_itanium_exception_ptr_cast(domain, bits, &typeid(reading)));
    if (!result || result->code != 47 ||
        __cxa_error_code_itanium_exception_ptr_cast(domain, bits, &typeid(unsigned)) ||
        __cxa_error_code_itanium_exception_ptr_cast(nullptr, bits, &typeid(device_error)))
        __builtin_trap();
    __cxxabiv1::__cxa_decrement_exception_refcount(owned);
#endif
}
