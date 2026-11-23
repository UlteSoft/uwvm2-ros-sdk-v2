/** Read-only projections of aimdk_msgs/JointState. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["str", 1, 0], // name
    ["f64", 1, 0], // position
    ["f64", 1, 0], // velocity
    ["f64", 1, 0], // effort
    ["u16", 1, 0], // error_code
];

/** Read position from the complete record. Invalid data or an invalid index returns undefined. */
export function read_position(data) {
    return project(data, 1, fields, 1, 0);
}

/** Read velocity from the complete record. Invalid data or an invalid index returns undefined. */
export function read_velocity(data) {
    return project(data, 1, fields, 2, 0);
}

/** Read effort from the complete record. Invalid data or an invalid index returns undefined. */
export function read_effort(data) {
    return project(data, 1, fields, 3, 0);
}

/** Read error_code from the complete record. Invalid data or an invalid index returns undefined. */
export function read_error_code(data) {
    return project(data, 1, fields, 4, 0);
}
