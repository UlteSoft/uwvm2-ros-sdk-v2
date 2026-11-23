/** Read-only projections of dsr_msgs/LogAlarm. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["i32", 1, 0], // level
    ["i32", 1, 0], // group
    ["i32", 1, 0], // index
    ["str", 3, 0], // param
];

/** Read level from the complete record. Invalid data or an invalid index returns undefined. */
export function read_level(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read group from the complete record. Invalid data or an invalid index returns undefined. */
export function read_group(data) {
    return project(data, 0, fields, 1, 0);
}

/** Read index from the complete record. Invalid data or an invalid index returns undefined. */
export function read_index(data) {
    return project(data, 0, fields, 2, 0);
}
