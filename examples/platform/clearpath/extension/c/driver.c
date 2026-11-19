/** @file driver.c
 * @brief Test that the platform child and the parent capability must both authorize driver connection.
 */
#include <stdint.h>
#include <wros/scene.h>

static const char alias[] = "arm";
/** @brief Open the assigned handle and verify that a denied connection preserves caller storage. */
void _start(void) {
    uint64_t handle = 0, reply = 0x4321, written = 0x1234;
    if (wr_capability_open(0, (uintptr_t)alias, sizeof alias-1, (uintptr_t)&handle) != 0) __builtin_trap();
    uint32_t status = wr_driver_connect(handle, 0, 0, 0, (uintptr_t)&reply, sizeof reply, (uintptr_t)&written);
    if (status != 13 || reply != 0x4321 || written != 0x1234 || wr_capability_close(handle) != 0) __builtin_trap();
}
