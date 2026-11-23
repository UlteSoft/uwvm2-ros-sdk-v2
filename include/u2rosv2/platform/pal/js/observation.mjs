/** Read-only projections of pal_device_msgs/BatteryState. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["i8", 1, 0], // charge_state
    ["f32", 1, 0], // battery_percentage
];

export const FULL = 5;
export const HIGH = 4;
export const MEDIUM = 3;
export const LOW = 2;
export const CRITICAL_LOW = 1;
/** Read charge_state from the complete record. Invalid data or an invalid index returns undefined. */
export function read_charge_state(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read battery_percentage from the complete record. Invalid data or an invalid index returns undefined. */
export function read_battery_percentage(data) {
    return project(data, 0, fields, 1, 0);
}
