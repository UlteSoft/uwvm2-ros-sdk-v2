import * as observation from "uwrosv2/platform/universal_robots/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0x03
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x03
]);

function check(data: Uint8Array): void {
    if (observation.read_status(data) !== 3) throw Error("status");
    if (observation.read_status(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated status");
}

check(sample);
check(bigEndian);
