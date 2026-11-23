#include <uwrosv2/capability.h>
#include <uwrosv2/guard.h>
#include <uwrosv2/resource.h>

static void require(int condition) {
    if (!condition) __builtin_trap();
}

void _start(void) {
    uwrosv2_capability full = {0}, limited = {0}, absent = {0};
    uwrosv2_resource first = {0}, second = {0};
    uint64_t count = 0;
    require(uwrosv2_abi() == 2);
    require(uwrosv2_capability_open(uwrosv2_string("absent", 6), &absent) == UWROSV2_DENIED);
    require(absent.id == 0);
    require(uwrosv2_capability_open(uwrosv2_string("signal", 6), &full) == UWROSV2_SUCCESS);
    require(uwrosv2_capability_open(uwrosv2_string("narrow", 6), &limited) == UWROSV2_SUCCESS);
    require(full.id != 0 && limited.id != 0 && full.id != limited.id);
    require(uwrosv2_guard_create(full, &first) == UWROSV2_SUCCESS);
    require(uwrosv2_guard_create(limited, &second) == UWROSV2_SUCCESS);
    require(uwrosv2_guard_trigger(limited, second) == UWROSV2_DENIED);
    require(uwrosv2_guard_trigger(full, first) == UWROSV2_SUCCESS);
    require(uwrosv2_guard_trigger(full, first) == UWROSV2_SUCCESS);
    require(uwrosv2_guard_take(full, first, &count) == UWROSV2_SUCCESS);
    require(count == 2);
    require(uwrosv2_guard_take(full, first, &count) == UWROSV2_AGAIN);
    require(uwrosv2_resource_close(limited, &second) == UWROSV2_SUCCESS && second.id == 0);
    require(uwrosv2_resource_close(full, &first) == UWROSV2_SUCCESS && first.id == 0);
    require(uwrosv2_capability_close(&limited) == UWROSV2_SUCCESS && limited.id == 0);
    require(uwrosv2_capability_close(&full) == UWROSV2_SUCCESS && full.id == 0);
}
