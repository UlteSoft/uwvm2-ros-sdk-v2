import * as observation from "uwrosv2/platform/ros1/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x2d, 0x01, 0x00, 0x00, 0x80, 0x17, 0xb4, 0x2c
]);

function check(data) {
    if (observation.read_data_sec(data) !== 301) throw Error("data_sec");
    if (observation.read_data_sec(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated data_sec");
    if (observation.read_data_nsec(data) !== 750000000) throw Error("data_nsec");
    if (observation.read_data_nsec(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated data_nsec");
}

check(sample);
