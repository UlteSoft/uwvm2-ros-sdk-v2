/** @file resource.c
 * @brief Check one pinned ROS package resource using guest-private memory.
 */
#include <stdint.h>
#include <wros/package_resources.h>
#include "selected_resource.h"

/** @brief Trap on a corrupt resource, an unexpected extra entry or an accepted miss. */
void _start(void) {
    static const unsigned char *volatile backing = resource_pack;
    wros_package_index index;
    wros_package_view view;
    if (!wros_package_open(backing, sizeof(resource_pack), &index) || index.count != 1)
        __builtin_trap();
    if (!wros_package_find(&index, resource_uri, sizeof(resource_uri) - 1, &view) ||
        view.size != RESOURCE_SIZE)
        __builtin_trap();
    uint32_t checksum = 2166136261u;
    for (size_t i = 0; i < view.size; ++i)
        checksum = (checksum ^ view.bytes[i]) * 16777619u;
    if (checksum != RESOURCE_CHECKSUM)
        __builtin_trap();
    const char absent[] = "package://wros_example_missing/resource";
    if (wros_package_find(&index, absent, sizeof(absent) - 1, &view) || view.bytes || view.size)
        __builtin_trap();
}
