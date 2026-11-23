/** Read-only projections of clearpath_dock_msgs/DockState. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u8", 1, 0], // state
];

export const UNDOCKED = 0;
export const DOCKED = 1;
export const IN_PROGRESS = 2;
export const FAILED = 3;
export const CANCELLED = 4;
/** Read state from the complete record. Invalid data or an invalid index returns undefined. */
export function read_state(data) {
    return project(data, 0, fields, 0, 0);
}
