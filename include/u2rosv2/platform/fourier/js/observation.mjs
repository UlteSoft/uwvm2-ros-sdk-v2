/** Read-only projections of simulator_pub_msg. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["i64", 1, 0], // timestamp
    ["i32", 1, 2], // motor_num
    ["f64", -1, 0], // q
    ["f64", -1, 0], // q_dot
    ["f64", 3, 0], // acc
    ["f64", 3, 0], // omega
    ["f64", 4, 0], // quat
    ["f64", 1, 0], // lf_touch
    ["f64", 1, 0], // rf_touch
    ["f64", 3, 0], // pos
    ["f64", 3, 0], // vel
];

/** Read timestamp from the complete record. Invalid data or an invalid index returns undefined. */
export function read_timestamp(data) {
    return project(data, 2, fields, 0, 0);
}

/** Read q from the complete record. Invalid data or an invalid index returns undefined. */
export function read_q(data, index) {
    return project(data, 2, fields, 2, index);
}

/** Read q_dot from the complete record. Invalid data or an invalid index returns undefined. */
export function read_q_dot(data, index) {
    return project(data, 2, fields, 3, index);
}

/** Read lf_touch from the complete record. Invalid data or an invalid index returns undefined. */
export function read_lf_touch(data) {
    return project(data, 2, fields, 7, 0);
}

/** Read rf_touch from the complete record. Invalid data or an invalid index returns undefined. */
export function read_rf_touch(data) {
    return project(data, 2, fields, 8, 0);
}
