#include <herbceptions/error>

extern "C" void _start() {
    using namespace std::error_domains;
    std::error_domain_singleton const* domains[] = {__cxa_error_domain_parse(), __cxa_error_domain_posix(),
                             __cxa_error_domain_cmath(), __cxa_error_domain_http(),
                             __cxa_error_domain_tls()};
    for (unsigned i = 0; i < 5; ++i) {
        if (!domains[i] || !std::is_valid_error_domain_singleton(*domains[i])) __builtin_trap();
        for (unsigned j = 0; j < i; ++j) if (domains[j] == domains[i]) __builtin_trap();
        if (!domains[i]->do_equivalent(3, domains[i], 3)) __builtin_trap();
        if (domains[i]->do_equivalent(3, domains[i], 4)) __builtin_trap();
    }
}
