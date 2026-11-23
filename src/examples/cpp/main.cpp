#include <uwrosv2/scene.hpp>

extern "C" void _start() UWROSV2_CPP_NOEXCEPT {
    if (uwrosv2::abi() != 2) __builtin_trap();
}
