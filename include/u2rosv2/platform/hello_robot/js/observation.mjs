/** Read-only projections of Wacc_Protocol_P0.unpack_status. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f32", 1, 0], // ax
    ["f32", 1, 0], // ay
    ["f32", 1, 0], // az
    ["i16", 1, 0], // a0
    ["u8", 1, 0], // d0
    ["u8", 1, 0], // d1
    ["u8", 1, 0], // d2
    ["u8", 1, 0], // d3
    ["u32", 1, 0], // single_tap_count
    ["u32", 1, 0], // state
    ["u32", 1, 0], // timestamp
    ["u32", 1, 0], // debug
];

/** Read ax from the complete record. Invalid data or an invalid index returns undefined. */
export function read_ax(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read az from the complete record. Invalid data or an invalid index returns undefined. */
export function read_az(data) {
    return project(data, 0, fields, 2, 0);
}

/** Read a0 from the complete record. Invalid data or an invalid index returns undefined. */
export function read_a0(data) {
    return project(data, 0, fields, 3, 0);
}

/** Read single_tap_count from the complete record. Invalid data or an invalid index returns undefined. */
export function read_single_tap_count(data) {
    return project(data, 0, fields, 8, 0);
}

/** Read timestamp from the complete record. Invalid data or an invalid index returns undefined. */
export function read_timestamp(data) {
    return project(data, 0, fields, 10, 0);
}
