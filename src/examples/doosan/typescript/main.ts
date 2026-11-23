import * as observation from "uwrosv2/platform/doosan/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x02, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 0xf9, 0xff, 0xff, 0xff,
    0x06, 0x00, 0x00, 0x00, 0x6a, 0x6f, 0x69, 0x6e, 0x74, 0x30, 0x06, 0x00,
    0x00, 0x00, 0x6a, 0x6f, 0x69, 0x6e, 0x74, 0x31, 0x06, 0x00, 0x00, 0x00,
    0x6a, 0x6f, 0x69, 0x6e, 0x74, 0x32
]);

function check(data: Uint8Array): void {
    if (observation.read_level(data) !== 2) throw Error("level");
    if (observation.read_level(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated level");
    if (observation.read_group(data) !== 3) throw Error("group");
    if (observation.read_group(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated group");
    if (observation.read_index(data) !== -7) throw Error("index");
    if (observation.read_index(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated index");
}

check(sample);
