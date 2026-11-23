/** Read-only projections of bosdyn.api.PointCloud.data. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f32", -4, 0], // xyz
];

/** Read xyz from the complete record. Invalid data or an invalid index returns undefined. */
export function read_x(data, index) {
    if (!Number.isSafeInteger(index) || index < 0) return undefined;
    return project(data, 0, fields, 0, index * 3 + 0);
}

/** Read xyz from the complete record. Invalid data or an invalid index returns undefined. */
export function read_y(data, index) {
    if (!Number.isSafeInteger(index) || index < 0) return undefined;
    return project(data, 0, fields, 0, index * 3 + 1);
}

/** Read xyz from the complete record. Invalid data or an invalid index returns undefined. */
export function read_z(data, index) {
    if (!Number.isSafeInteger(index) || index < 0) return undefined;
    return project(data, 0, fields, 0, index * 3 + 2);
}
