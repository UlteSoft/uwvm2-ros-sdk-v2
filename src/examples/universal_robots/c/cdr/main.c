#include <uwrosv2/universal_robots/cdr/ur_dashboard_msgs.h>
#include "program_information_frames.h"

typedef uwrosv2_universal_robots_cdr_ur_dashboard_msgs_ProgramInformation ProgramInformation;

static int transcode(const volatile uint8_t *source, const uint8_t *expected,
                     uwrosv2_universal_robots_cdr_endian order) {
    uint8_t input[sizeof metadata_big], output[sizeof metadata_big];
    for (size_t i = 0; i < sizeof input; ++i) input[i] = source[i];

    ProgramInformation value;
    if (!uwrosv2_universal_robots_cdr_ur_dashboard_msgs_ProgramInformation_decode(input, sizeof input, &value))
        return 0;

    const uwrosv2_universal_robots_cdr_string final_state =
        uwrosv2_universal_robots_cdr_ur_dashboard_msgs_ProgramInformation_PROGRAM_STATE_FINAL;
    if (value.name.size != 1 || value.name.data[0] != 'A' ||
        value.description.size != 2 || memcmp(value.description.data, "BC", 2) != 0 ||
        value.created_date != UINT64_C(0x0102030405060708) ||
        value.last_saved_date != UINT64_C(0x8000000000000001) ||
        value.last_modified_date != UINT64_C(0xfedcba9876543210) ||
        value.program_state.size != final_state.size ||
        memcmp(value.program_state.data, final_state.data, final_state.size) != 0) return 0;

    size_t size, written;
    return uwrosv2_universal_robots_cdr_ur_dashboard_msgs_ProgramInformation_encoded_size(&value, &size)
        && size == sizeof output
        && uwrosv2_universal_robots_cdr_ur_dashboard_msgs_ProgramInformation_encode(
            &value, order, output, sizeof output, &written)
        && written == size && memcmp(output, expected, written) == 0
        && !uwrosv2_universal_robots_cdr_ur_dashboard_msgs_ProgramInformation_validate(input, sizeof input - 1);
}

void _start(void) {
    if (!transcode(metadata_big, metadata_little, uwrosv2_universal_robots_cdr_little_endian) ||
        !transcode(metadata_little, metadata_big, uwrosv2_universal_robots_cdr_big_endian))
        __builtin_trap();
}
