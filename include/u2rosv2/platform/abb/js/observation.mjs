/** Read-only projections of abb_rapid_msgs/Pos. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f32", 1, 0], // x
    ["f32", 1, 0], // y
    ["f32", 1, 0], // z
];

/** Read x from the complete record. Invalid data or an invalid index returns undefined. */
export function read_x(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read y from the complete record. Invalid data or an invalid index returns undefined. */
export function read_y(data) {
    return project(data, 0, fields, 1, 0);
}

/** Read z from the complete record. Invalid data or an invalid index returns undefined. */
export function read_z(data) {
    return project(data, 0, fields, 2, 0);
}
