import * as observation from "uwrosv2/platform/limx/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x0c, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x05, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xe4, 0x3f, 0x05, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61,
    0x6d, 0x65
]);

function check(data: Uint8Array): void {
    if (observation.read_estimate_height(data) !== 0.625) throw Error("estimate_height");
    if (observation.read_estimate_height(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated estimate_height");
    if (observation.read_header_seq(data) !== 524) throw Error("header_seq");
    if (observation.read_header_seq(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated header_seq");
}

check(sample);
