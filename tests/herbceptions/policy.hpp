#pragma once

#if !defined(__HERBCEPTIONS__) || __HERBCEPTIONS__ != 1
#error "the selected frontend must implement Herbceptions"
#endif

using word = __SIZE_TYPE__;
namespace std {
struct error { const void* domain; word code; };
}
namespace fixture {
struct reading { unsigned value; unsigned channel; };
struct failure { unsigned code; unsigned channel; };
extern const int sensor_domain;
extern unsigned cleanups;
reading measure(unsigned channel) throws;
reading forward(unsigned channel) throws;
reading sample(unsigned channel) return_failure{failure};
void standard_failure();

static_assert(__is_invoke_herbceptions_return_failure(decltype(sample)));
static_assert(!__is_invoke_herbceptions_return_failure(decltype(measure)));
static_assert(__is_same(__invoke_herbceptions_return_failure_t(decltype(sample)), failure));
static_assert(__is_same(__invoke_herbceptions_return_failure_t(decltype(measure)), void));
static_assert(__is_herbceptions_throws_invocable(decltype(measure), unsigned));
static_assert(!__is_herbceptions_throws_invocable(decltype(standard_failure)));
}
