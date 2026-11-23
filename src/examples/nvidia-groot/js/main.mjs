import * as observation from "uwrosv2/platform/nvidia-groot/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3e, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x40, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0xbe,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
]);

function check(data) {
    if (observation.read_eef_9d(data, 1) !== 0.125) throw Error("eef_9d");
    if (observation.read_eef_9d(data.subarray(0, data.length - 1), 1) !== undefined) throw Error("truncated eef_9d");
    if (observation.read_eef_9d(data, -1) !== undefined) throw Error("invalid index");
    if (observation.read_gripper_position(data) !== 0.75) throw Error("gripper_position");
    if (observation.read_gripper_position(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated gripper_position");
    if (observation.read_joint_position(data, 1) !== -0.25) throw Error("joint_position");
    if (observation.read_joint_position(data.subarray(0, data.length - 1), 1) !== undefined) throw Error("truncated joint_position");
    if (observation.read_joint_position(data, -1) !== undefined) throw Error("invalid index");
}

check(sample);
