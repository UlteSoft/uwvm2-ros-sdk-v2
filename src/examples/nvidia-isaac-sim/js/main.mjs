import * as observation from "uwrosv2/platform/nvidia-isaac-sim/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0x05, 0x00, 0x00, 0x00, 0xa0, 0xac, 0xb9, 0x03
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05, 0x03, 0xb9, 0xac, 0xa0
]);

function check(data) {
    if (observation.read_clock_sec(data) !== 5) throw Error("clock_sec");
    if (observation.read_clock_sec(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated clock_sec");
    if (observation.read_clock_nanosec(data) !== 62500000) throw Error("clock_nanosec");
    if (observation.read_clock_nanosec(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated clock_nanosec");
}

check(sample);
check(bigEndian);
