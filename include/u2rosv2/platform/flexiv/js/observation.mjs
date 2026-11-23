/** Read-only projections of flexiv_msgs/Digital. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u8", 1, 0], // pin
    ["bool", 1, 1], // state
];

/** Read pin from the complete record. Invalid data or an invalid index returns undefined. */
export function read_pin(data) {
    return project(data, 1, fields, 0, 0);
}

/** Read state from the complete record. Invalid data or an invalid index returns undefined. */
export function read_state(data) {
    return project(data, 1, fields, 1, 0);
}
