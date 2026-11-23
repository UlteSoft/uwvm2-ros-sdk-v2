import * as observation from "uwrosv2/platform/robotis/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x05, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61, 0x6d, 0x65, 0x03, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x97, 0xff, 0xff, 0xff, 0x2c, 0x01, 0x00, 0x00, 0x00, 0x00, 0x44,
    0x41
]);

function check(data: Uint8Array): void {
    if (observation.read_bumper(data) !== 3) throw Error("bumper");
    if (observation.read_bumper(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated bumper");
    if (observation.read_left_encoder(data) !== -105) throw Error("left_encoder");
    if (observation.read_left_encoder(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated left_encoder");
    if (observation.read_right_encoder(data) !== 300) throw Error("right_encoder");
    if (observation.read_right_encoder(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated right_encoder");
    if (observation.read_battery(data) !== 12.25) throw Error("battery");
    if (observation.read_battery(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated battery");
}

check(sample);
