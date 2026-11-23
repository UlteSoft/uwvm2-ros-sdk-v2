import * as observation from "uwrosv2/platform/hello_robot/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x00, 0x00, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x41,
    0x88, 0xff, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x78, 0x56, 0x34, 0x12, 0x00, 0x00, 0x00, 0x00
]);

function check(data: Uint8Array): void {
    if (observation.read_ax(data) !== 0.5) throw Error("ax");
    if (observation.read_ax(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated ax");
    if (observation.read_az(data) !== 9.5) throw Error("az");
    if (observation.read_az(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated az");
    if (observation.read_a0(data) !== -120) throw Error("a0");
    if (observation.read_a0(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated a0");
    if (observation.read_single_tap_count(data) !== 513) throw Error("single_tap_count");
    if (observation.read_single_tap_count(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated single_tap_count");
    if (observation.read_timestamp(data) !== 305419896) throw Error("timestamp");
    if (observation.read_timestamp(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated timestamp");
}

check(sample);
