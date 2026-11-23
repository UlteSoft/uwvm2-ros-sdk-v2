import * as observation from "uwrosv2/platform/dobot/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0x00, 0x01
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x01
]);

function check(data: Uint8Array): void {
    if (observation.read_is_enable(data) !== false) throw Error("is_enable");
    if (observation.read_is_enable(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated is_enable");
    if (observation.read_is_connected(data) !== true) throw Error("is_connected");
    if (observation.read_is_connected(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated is_connected");
}

check(sample);
check(bigEndian);
