/** Read-only projections of booster_interface/ImuState. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f32", 3, 0], // rpy
    ["f32", 3, 0], // gyro
    ["f32", 3, 0], // acc
];

/** Read rpy from the complete record. Invalid data or an invalid index returns undefined. */
export function read_rpy(data, index) {
    return project(data, 1, fields, 0, index);
}

/** Read gyro from the complete record. Invalid data or an invalid index returns undefined. */
export function read_gyro(data, index) {
    return project(data, 1, fields, 1, index);
}

/** Read acc from the complete record. Invalid data or an invalid index returns undefined. */
export function read_acc(data, index) {
    return project(data, 1, fields, 2, index);
}
