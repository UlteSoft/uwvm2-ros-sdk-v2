/** Read-only projections of franka_msgs/Elbow. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f64", 2, 0], // position
    ["f64", 2, 0], // desired_position
    ["f64", 2, 0], // commanded_position
    ["f64", 2, 0], // commanded_velocity
    ["f64", 2, 0], // commanded_acceleration
];

/** Read position from the complete record. Invalid data or an invalid index returns undefined. */
export function read_position(data, index) {
    return project(data, 1, fields, 0, index);
}

/** Read desired_position from the complete record. Invalid data or an invalid index returns undefined. */
export function read_desired_position(data, index) {
    return project(data, 1, fields, 1, index);
}

/** Read commanded_position from the complete record. Invalid data or an invalid index returns undefined. */
export function read_commanded_position(data, index) {
    return project(data, 1, fields, 2, index);
}

/** Read commanded_velocity from the complete record. Invalid data or an invalid index returns undefined. */
export function read_commanded_velocity(data, index) {
    return project(data, 1, fields, 3, index);
}

/** Read commanded_acceleration from the complete record. Invalid data or an invalid index returns undefined. */
export function read_commanded_acceleration(data, index) {
    return project(data, 1, fields, 4, index);
}
