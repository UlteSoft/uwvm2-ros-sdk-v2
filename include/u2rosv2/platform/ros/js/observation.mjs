/** Read-only projections of geometry_msgs/Quaternion. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f64", 1, 0], // x
    ["f64", 1, 0], // y
    ["f64", 1, 0], // z
    ["f64", 1, 0], // w
];

/** Read x from the complete record. Invalid data or an invalid index returns undefined. */
export function read_x(data) {
    return project(data, 3, fields, 0, 0);
}

/** Read y from the complete record. Invalid data or an invalid index returns undefined. */
export function read_y(data) {
    return project(data, 3, fields, 1, 0);
}

/** Read z from the complete record. Invalid data or an invalid index returns undefined. */
export function read_z(data) {
    return project(data, 3, fields, 2, 0);
}

/** Read w from the complete record. Invalid data or an invalid index returns undefined. */
export function read_w(data) {
    return project(data, 3, fields, 3, 0);
}
