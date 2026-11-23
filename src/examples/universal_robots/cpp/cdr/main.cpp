#include <uwrosv2/universal_robots/cdr/ur_dashboard_msgs.hpp>
#include "program_information_frames.h"

namespace cdr = uwrosv2::universal_robots::cdr;
namespace dashboard = cdr::ur_dashboard_msgs;

static bool transcode(const volatile uint8_t *source, const uint8_t *expected, cdr::endian order) {
    uint8_t input[sizeof metadata_big], output[sizeof metadata_big];
    for (size_t i = 0; i < sizeof input; ++i) input[i] = source[i];

    dashboard::ProgramInformation value;
    if (!cdr::decode(input, sizeof input, value)) return false;

    const cdr::string final_state = dashboard::ProgramInformation_Constants::PROGRAM_STATE_FINAL;
    if (value.name.size != 1 || value.name.data[0] != 'A' ||
        value.description.size != 2 || memcmp(value.description.data, "BC", 2) != 0 ||
        value.created_date != ((uint64_t(0x01020304u) << 32) | 0x05060708u) ||
        value.last_saved_date != ((uint64_t(0x80000000u) << 32) | 1u) ||
        value.last_modified_date != ((uint64_t(0xfedcba98u) << 32) | 0x76543210u) ||
        value.program_state.size != final_state.size ||
        memcmp(value.program_state.data, final_state.data, final_state.size) != 0) return false;

    size_t size, written;
    return cdr::encoded_size(value, size) && size == sizeof output
        && cdr::encode(value, order, output, sizeof output, written)
        && written == size && memcmp(output, expected, written) == 0
        && !cdr::validate<dashboard::ProgramInformation>(input, sizeof input - 1);
}

extern "C" void _start() {
    if (!transcode(metadata_big, metadata_little, cdr::little_endian) ||
        !transcode(metadata_little, metadata_big, cdr::big_endian)) __builtin_trap();
}
