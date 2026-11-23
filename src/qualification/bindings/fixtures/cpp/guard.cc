#include <uwrosv2/capability.hpp>
#include <uwrosv2/guard.hpp>
#include <uwrosv2/resource.hpp>

static void require(bool condition) {
    if (!condition) __builtin_trap();
}

extern "C" void _start() {
    namespace ros = uwrosv2;
    constexpr auto success = static_cast<uint32_t>(ros::status::success);
    constexpr auto denied = static_cast<uint32_t>(ros::status::denied);
    constexpr auto again = static_cast<uint32_t>(ros::status::again);
    require(ros::abi() == 2);
    const auto absent = ros::capability::open("absent");
    require(absent.call.status == denied && absent.value.id == 0);
    auto full = ros::capability::open("signal");
    auto limited = ros::capability::open("narrow");
    require(full && limited && full.value.id && limited.value.id && full.value.id != limited.value.id);
    auto first = ros::guard::create(full.value);
    auto second = ros::guard::create(limited.value);
    require(first && second);
    require(ros::guard::trigger(limited.value, second.value) == denied);
    require(ros::guard::trigger(full.value, first.value) == success);
    require(ros::guard::trigger(full.value, first.value) == success);
    auto count = ros::guard::take(full.value, first.value);
    require(count && count.value == 2);
    require(ros::guard::take(full.value, first.value).call.status == again);
    require(ros::resource::close(limited.value, second.value) == success && second.value.id == 0);
    require(ros::resource::close(full.value, first.value) == success && first.value.id == 0);
    require(ros::capability::close(limited.value) == success && limited.value.id == 0);
    require(ros::capability::close(full.value) == success && full.value.id == 0);
}
