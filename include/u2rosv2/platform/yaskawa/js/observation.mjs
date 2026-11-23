/** Read-only projections of motoros2_interfaces/ErrorInfo. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u32", 1, 0], // number
    ["str", 1, 0], // message
    ["i32", 1, 0], // sub_code
    ["i32", 1, 0], // datetime_sec
    ["u32", 1, 0], // datetime_nanosec
];

/** Read number from the complete record. Invalid data or an invalid index returns undefined. */
export function read_number(data) {
    return project(data, 1, fields, 0, 0);
}

/** Read sub_code from the complete record. Invalid data or an invalid index returns undefined. */
export function read_sub_code(data) {
    return project(data, 1, fields, 2, 0);
}

/** Read datetime_sec from the complete record. Invalid data or an invalid index returns undefined. */
export function read_datetime_sec(data) {
    return project(data, 1, fields, 3, 0);
}

/** Read datetime_nanosec from the complete record. Invalid data or an invalid index returns undefined. */
export function read_datetime_nanosec(data) {
    return project(data, 1, fields, 4, 0);
}
