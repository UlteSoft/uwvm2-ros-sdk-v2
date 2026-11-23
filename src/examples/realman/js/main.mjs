import * as observation from "uwrosv2/platform/realman/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x01, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x01,
    0x02
]);

const bigEndian = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x01, 0x02,
    0x02
]);

function check(data) {
    if (observation.read_joint_error(data, 1) !== 258) throw Error("joint_error");
    if (observation.read_joint_error(data.subarray(0, data.length - 1), 1) !== undefined) throw Error("truncated joint_error");
    if (observation.read_joint_error(data, -1) !== undefined) throw Error("invalid index");
    if (observation.read_dof(data) !== 2) throw Error("dof");
    if (observation.read_dof(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated dof");
}

check(sample);
check(bigEndian);
