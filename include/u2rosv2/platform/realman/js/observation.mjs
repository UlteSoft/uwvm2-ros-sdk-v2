/** Read-only projections of rm_ros_interfaces/Jointerrorcode. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u16", 0, 0], // joint_error
    ["u8", 1, 0], // dof
];

/** Read joint_error from the complete record. Invalid data or an invalid index returns undefined. */
export function read_joint_error(data, index) {
    return project(data, 1, fields, 0, index);
}

/** Read dof from the complete record. Invalid data or an invalid index returns undefined. */
export function read_dof(data) {
    return project(data, 1, fields, 1, 0);
}
