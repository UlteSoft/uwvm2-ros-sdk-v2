/** Read-only projections of xarm_msgs/IOState. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["i32", 1, 0], // digital_1
    ["i32", 1, 0], // digital_2
    ["f32", 1, 0], // analog_1
    ["f32", 1, 0], // analog_2
];

/** Read digital_1 from the complete record. Invalid data or an invalid index returns undefined. */
export function read_digital_1(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read digital_2 from the complete record. Invalid data or an invalid index returns undefined. */
export function read_digital_2(data) {
    return project(data, 0, fields, 1, 0);
}

/** Read analog_1 from the complete record. Invalid data or an invalid index returns undefined. */
export function read_analog_1(data) {
    return project(data, 0, fields, 2, 0);
}

/** Read analog_2 from the complete record. Invalid data or an invalid index returns undefined. */
export function read_analog_2(data) {
    return project(data, 0, fields, 3, 0);
}
