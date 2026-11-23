import * as observation from "uwrosv2/platform/abb/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x00, 0x48, 0x41, 0x00, 0x00, 0x30, 0xc0, 0x00, 0x00, 0x00, 0x3f
]);

function check(data) {
    if (observation.read_x(data) !== 12.5) throw Error("x");
    if (observation.read_x(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated x");
    if (observation.read_y(data) !== -2.75) throw Error("y");
    if (observation.read_y(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated y");
    if (observation.read_z(data) !== 0.5) throw Error("z");
    if (observation.read_z(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated z");
}

check(sample);
