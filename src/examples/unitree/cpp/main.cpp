#include <uwrosv2/base.hpp>
#include <uwrosv2/unitree/go2_low_state.hpp>

static const volatile uint64_t sequence = 7;
static const volatile uint8_t recorded[40] = {
    0, 0, 0, 0, 0, 0, 0, 0,  24, 0, 0, 0, 0, 0, 0, 0,
    16, 0, 0, 0, 0, 0, 0, 0, 0x83, 0xa1, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0x3e, 0, 0, 0, 0
};

extern "C" void _start() UWROSV2_CPP_NOEXCEPT {
    using namespace uwrosv2::unitree;
    uint8_t request[read_size];
    if (!encode_read(sequence, 1024, request, sizeof request) ||
        request[0] != 7 || request[9] != 4 || request[16] != 24 || request[24] != 1 || request[40] != 16)
        __builtin_trap();
    uint8_t response[result_size];
    for (size_t i = 0; i < sizeof response; ++i) response[i] = recorded[i];
    low_state sample;
    if (!decode_result(response, sizeof response, sample) || sample.tick != 41347 || sample.first_joint_position != 0.125f)
        __builtin_trap();
    response[8] = 0;
    if (decode_result(response, sizeof response, sample)) __builtin_trap();
}
