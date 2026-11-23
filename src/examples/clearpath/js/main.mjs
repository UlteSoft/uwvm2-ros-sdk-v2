import * as observation from "uwrosv2/platform/clearpath/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x03
]);

function check(data) {
    if (observation.read_state(data) !== 3) throw Error("state");
    if (observation.read_state(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated state");
}

check(sample);
