/** Read-only projections of std_msgs/Time. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u32", 1, 0], // data_sec
    ["u32", 1, 0], // data_nsec
];

/** Read data_sec from the complete record. Invalid data or an invalid index returns undefined. */
export function read_data_sec(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read data_nsec from the complete record. Invalid data or an invalid index returns undefined. */
export function read_data_nsec(data) {
    return project(data, 0, fields, 1, 0);
}
