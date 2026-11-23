#include <uwrosv2/unitree/go2_low_state.h>

static const volatile uint64_t sequence = 7;
static const volatile uint8_t recorded[UWROSV2_GO2_RESULT_BYTES] = {
    [8] = 24, [16] = 16, [24] = 0x83, [25] = 0xa1, [35] = 0x3e
};

void _start(void) {
    uint8_t request[UWROSV2_GO2_READ_BYTES];
    if (!uwrosv2_go2_encode_read(sequence, 1024, request, sizeof request) ||
        request[0] != 7 || request[9] != 4 || request[16] != 24 || request[24] != 1 || request[40] != 16)
        __builtin_trap();
    uint8_t frame[UWROSV2_GO2_RESULT_BYTES];
    for (size_t i = 0; i < sizeof frame; ++i) frame[i] = recorded[i];
    uwrosv2_go2_low_state sample;
    if (!uwrosv2_go2_decode_result(frame, sizeof frame, &sample) ||
        sample.tick != 41347 || sample.first_joint_position != 0.125f ||
        uwrosv2_go2_decode_result(frame, sizeof frame - 1, &sample)) __builtin_trap();
}
