import * as observation from "uwrosv2/platform/ufactory/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa0, 0x3f,
    0x00, 0x00, 0x60, 0x40
]);

function check(data) {
    if (observation.read_digital_1(data) !== 1) throw Error("digital_1");
    if (observation.read_digital_1(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated digital_1");
    if (observation.read_digital_2(data) !== 0) throw Error("digital_2");
    if (observation.read_digital_2(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated digital_2");
    if (observation.read_analog_1(data) !== 1.25) throw Error("analog_1");
    if (observation.read_analog_1(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated analog_1");
    if (observation.read_analog_2(data) !== 3.5) throw Error("analog_2");
    if (observation.read_analog_2(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated analog_2");
}

check(sample);
