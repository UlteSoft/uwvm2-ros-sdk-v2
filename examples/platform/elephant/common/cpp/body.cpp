/** @file body.cpp
 * @brief Read the explicitly exposed ROSv2 ABI from a C++ guest.
 */
#include <wros/scene.h>
extern "C" void _start() {
    if (wr_abi() != 2) __builtin_trap();
}
