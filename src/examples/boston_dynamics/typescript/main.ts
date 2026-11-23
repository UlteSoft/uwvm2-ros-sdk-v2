import * as observation from "uwrosv2/platform/boston_dynamics/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xbf, 0x00, 0x00, 0xa0, 0x3f, 0x00, 0x00, 0x40, 0x3f
]);

function check(data: Uint8Array): void {
    if (observation.read_x(data, 1) !== -0.5) throw Error("x");
    if (observation.read_x(data.subarray(0, data.length - 1), 1) !== undefined) throw Error("truncated x");
    if (observation.read_x(data, -1) !== undefined) throw Error("invalid index");
    if (observation.read_y(data, 1) !== 1.25) throw Error("y");
    if (observation.read_y(data.subarray(0, data.length - 1), 1) !== undefined) throw Error("truncated y");
    if (observation.read_y(data, -1) !== undefined) throw Error("invalid index");
    if (observation.read_z(data, 1) !== 0.75) throw Error("z");
    if (observation.read_z(data.subarray(0, data.length - 1), 1) !== undefined) throw Error("truncated z");
    if (observation.read_z(data, -1) !== undefined) throw Error("invalid index");
}

check(sample);
