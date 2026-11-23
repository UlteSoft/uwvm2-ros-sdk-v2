/** Read-only projections of fanuc_msgs/ForceSensor. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f32", 1, 0], // force_x
    ["f32", 1, 0], // force_y
    ["f32", 1, 0], // force_z
    ["f32", 1, 0], // moment_x
    ["f32", 1, 0], // moment_y
    ["f32", 1, 0], // moment_z
    ["u32", 1, 0], // fs_type
];

/** Read force_x from the complete record. Invalid data or an invalid index returns undefined. */
export function read_force_x(data) {
    return project(data, 1, fields, 0, 0);
}

/** Read force_z from the complete record. Invalid data or an invalid index returns undefined. */
export function read_force_z(data) {
    return project(data, 1, fields, 2, 0);
}

/** Read moment_z from the complete record. Invalid data or an invalid index returns undefined. */
export function read_moment_z(data) {
    return project(data, 1, fields, 5, 0);
}

/** Read fs_type from the complete record. Invalid data or an invalid index returns undefined. */
export function read_fs_type(data) {
    return project(data, 1, fields, 6, 0);
}
