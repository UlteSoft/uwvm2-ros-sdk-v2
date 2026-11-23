import * as observation from "uwrosv2/platform/elephant/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x01, 0xff, 0x02
]);

function check(data) {
    if (observation.read_status(data) !== true) throw Error("status");
    if (observation.read_status(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated status");
    if (observation.read_pin1(data) !== -1) throw Error("pin1");
    if (observation.read_pin1(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated pin1");
    if (observation.read_pin2(data) !== 2) throw Error("pin2");
    if (observation.read_pin2(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated pin2");
}

check(sample);
