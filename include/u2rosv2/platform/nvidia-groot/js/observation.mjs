/** Read-only projections of DROID observation.state. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f32", 9, 0], // eef_9d
    ["f32", 1, 0], // gripper_position
    ["f32", 7, 0], // joint_position
];

/** Read eef_9d from the complete record. Invalid data or an invalid index returns undefined. */
export function read_eef_9d(data, index) {
    return project(data, 0, fields, 0, index);
}

/** Read gripper_position from the complete record. Invalid data or an invalid index returns undefined. */
export function read_gripper_position(data) {
    return project(data, 0, fields, 1, 0);
}

/** Read joint_position from the complete record. Invalid data or an invalid index returns undefined. */
export function read_joint_position(data, index) {
    return project(data, 0, fields, 2, index);
}
