/** Read-only projections of drdds/ImuDataValue. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f32", 1, 0], // roll
    ["f32", 1, 0], // pitch
    ["f32", 1, 0], // yaw
    ["f32", 1, 0], // omega_x
    ["f32", 1, 0], // omega_y
    ["f32", 1, 0], // omega_z
    ["f32", 1, 0], // acc_x
    ["f32", 1, 0], // acc_y
    ["f32", 1, 0], // acc_z
];

/** Read roll from the complete record. Invalid data or an invalid index returns undefined. */
export function read_roll(data) {
    return project(data, 1, fields, 0, 0);
}

/** Read yaw from the complete record. Invalid data or an invalid index returns undefined. */
export function read_yaw(data) {
    return project(data, 1, fields, 2, 0);
}

/** Read omega_z from the complete record. Invalid data or an invalid index returns undefined. */
export function read_omega_z(data) {
    return project(data, 1, fields, 5, 0);
}

/** Read acc_z from the complete record. Invalid data or an invalid index returns undefined. */
export function read_acc_z(data) {
    return project(data, 1, fields, 8, 0);
}
