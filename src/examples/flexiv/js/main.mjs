import * as observation from "uwrosv2/platform/flexiv/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0x06, 0x01
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x06, 0x01
]);

function check(data) {
    if (observation.read_pin(data) !== 6) throw Error("pin");
    if (observation.read_pin(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated pin");
    if (observation.read_state(data) !== true) throw Error("state");
    if (observation.read_state(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated state");
}

check(sample);
check(bigEndian);
