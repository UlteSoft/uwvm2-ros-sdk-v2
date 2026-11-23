/** Read-only projections of myarm_communication/MyArmPumpStatus. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["bool", 1, 1], // status
    ["i8", 1, 0], // pin1
    ["i8", 1, 0], // pin2
];

/** Read status from the complete record. Invalid data or an invalid index returns undefined. */
export function read_status(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read pin1 from the complete record. Invalid data or an invalid index returns undefined. */
export function read_pin1(data) {
    return project(data, 0, fields, 1, 0);
}

/** Read pin2 from the complete record. Invalid data or an invalid index returns undefined. */
export function read_pin2(data) {
    return project(data, 0, fields, 2, 0);
}
