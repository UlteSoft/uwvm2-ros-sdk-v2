/** Read-only projections of builtin_interfaces/Duration. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["i32", 1, 0], // sec
    ["u32", 1, 0], // nanosec
];

/** Read sec from the complete record. Invalid data or an invalid index returns undefined. */
export function read_sec(data) {
    return project(data, 1, fields, 0, 0);
}

/** Read nanosec from the complete record. Invalid data or an invalid index returns undefined. */
export function read_nanosec(data) {
    return project(data, 1, fields, 1, 0);
}
