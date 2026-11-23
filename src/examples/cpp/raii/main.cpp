#include <uwrosv2/guard.hpp>

namespace ros = uwrosv2;

// A borrowed guard and its capability must come from the same VM grant.
static uint32_t signal_once(const ros::resource_owner& signal) UWROSV2_CPP_NOEXCEPT {
    const uint32_t code = ros::guard::trigger(signal.capability(), signal.get());
    if (code) return code;
    const ros::result<uint64_t> count = ros::guard::take(signal.capability(), signal.get());
    if (!count) return count.call.status;
    return count.value == 1 ? 0 : static_cast<uint32_t>(ros::status::invalid);
}

static uint32_t open_signal(ros::resource_owner& destination) UWROSV2_CPP_NOEXCEPT {
    ros::capability_owner grant;
    uint32_t code = grant.open("signal");
    if (code) return code;

    ros::resource_owner signal;
    code = ros::guard::create(grant.get(), signal);
    if (code) return code;
    {
        // Both guards borrow the same capability. Scope exit closes the short-lived guard.
        ros::resource_owner startup;
        code = ros::guard::create(grant.get(), startup);
        if (code) return code;
        code = signal_once(startup);
        if (code) return code;
    }
    // The remaining guard leaves this function together with its issuing capability.
    code = signal.take_capability(grant);
    if (code) return code;
    return signal.transfer_to(destination);
}

static uint32_t run() UWROSV2_CPP_NOEXCEPT {
    ros::resource_owner signal;
    uint32_t code = open_signal(signal);
    if (code) return code;
    code = signal_once(signal);
    if (code) return code;
    return signal.close();  // Report failure to the caller. Scope exit handles early returns.
}

extern "C" void _start() UWROSV2_CPP_NOEXCEPT {
    if (run()) __builtin_trap();
}
