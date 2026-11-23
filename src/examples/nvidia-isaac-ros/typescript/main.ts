import * as observation from "uwrosv2/platform/nvidia-isaac-ros/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x80, 0x02, 0x00, 0x00
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x80
]);

function check(data: Uint8Array): void {
    if (observation.read_rank(data) !== 2) throw Error("rank");
    if (observation.read_rank(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated rank");
    if (observation.read_dims(data, 1) !== 640) throw Error("dims");
    if (observation.read_dims(data.subarray(0, data.length - 1), 1) !== undefined) throw Error("truncated dims");
    if (observation.read_dims(data, -1) !== undefined) throw Error("invalid index");
}

check(sample);
check(bigEndian);
