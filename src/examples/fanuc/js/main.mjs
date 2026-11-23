import * as observation from "uwrosv2/platform/fanuc/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x20, 0xc0, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x04, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xbe, 0x02, 0x00, 0x00, 0x00
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0xc0, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x41, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xbe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02
]);

function check(data) {
    if (observation.read_force_x(data) !== -2.5) throw Error("force_x");
    if (observation.read_force_x(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated force_x");
    if (observation.read_force_z(data) !== 8.25) throw Error("force_z");
    if (observation.read_force_z(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated force_z");
    if (observation.read_moment_z(data) !== -0.125) throw Error("moment_z");
    if (observation.read_moment_z(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated moment_z");
    if (observation.read_fs_type(data) !== 2) throw Error("fs_type");
    if (observation.read_fs_type(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated fs_type");
}

check(sample);
check(bigEndian);
