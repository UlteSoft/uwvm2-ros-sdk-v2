#include "policy.hpp"

namespace fixture {
constexpr unsigned require_channel(unsigned channel) return_failure{unsigned} {
    if (channel > 7) return_failure(100 + channel);
    return channel;
}
constexpr unsigned checked_channel(unsigned channel) {
    if (channel == 0) return 0;
    auto result = catch return_failure(require_channel(channel));
    return result.failed ? result.error : result.value;
}
static_assert(checked_channel(2) == 2);
static_assert(checked_channel(9) == 109);

const int sensor_domain = 0;
unsigned cleanups = 0;
struct lease {
    ~lease() { ++cleanups; }
};

reading measure(unsigned channel) throws {
    lease session;
    if (channel > 7) throw throws std::error{&sensor_domain, 100 + channel};
    return {42 + channel, channel};
}

reading sample(unsigned channel) return_failure{failure} {
    lease session;
    if (channel > 7) return_failure(failure{700 + channel, channel});
    return {80 + channel, channel};
}

#if defined(__cpp_exceptions)
void standard_failure() {
    lease session;
    throw 31;
}
#endif
}
