/** Read-only projections of interbotix_xs_msgs/JointTemps. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["str", 0, 0], // names
    ["i32", 0, 0], // temps
];

/** Read temps from the complete record. Invalid data or an invalid index returns undefined. */
export function read_temps(data, index) {
    return project(data, 0, fields, 1, index);
}
