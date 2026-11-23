import * as observation from "uwrosv2/platform/ros2/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0xfe, 0xff, 0xff, 0xff, 0x00, 0xa3, 0xe1, 0x11
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xfe, 0x11, 0xe1, 0xa3, 0x00
]);

function check(data) {
    if (observation.read_sec(data) !== -2) throw Error("sec");
    if (observation.read_sec(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated sec");
    if (observation.read_nanosec(data) !== 300000000) throw Error("nanosec");
    if (observation.read_nanosec(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated nanosec");
}

check(sample);
check(bigEndian);
