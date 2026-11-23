import * as observation from "uwrosv2/platform/yaskawa/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0x03, 0x04, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00,
    0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00, 0xfe, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xe8, 0x03, 0x00, 0x00
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x03, 0x00, 0x00, 0x00, 0x06,
    0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x03, 0xe8
]);

function check(data: Uint8Array): void {
    if (observation.read_number(data) !== 1027) throw Error("number");
    if (observation.read_number(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated number");
    if (observation.read_sub_code(data) !== -2) throw Error("sub_code");
    if (observation.read_sub_code(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated sub_code");
    if (observation.read_datetime_sec(data) !== -1) throw Error("datetime_sec");
    if (observation.read_datetime_sec(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated datetime_sec");
    if (observation.read_datetime_nanosec(data) !== 1000) throw Error("datetime_nanosec");
    if (observation.read_datetime_nanosec(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated datetime_nanosec");
}

check(sample);
check(bigEndian);
