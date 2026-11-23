/** Read-only projections of dobot_msgs_v4/RobotStatus. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["bool", 1, 1], // is_enable
    ["bool", 1, 1], // is_connected
];

/** Read is_enable from the complete record. Invalid data or an invalid index returns undefined. */
export function read_is_enable(data) {
    return project(data, 1, fields, 0, 0);
}

/** Read is_connected from the complete record. Invalid data or an invalid index returns undefined. */
export function read_is_connected(data) {
    return project(data, 1, fields, 1, 0);
}
