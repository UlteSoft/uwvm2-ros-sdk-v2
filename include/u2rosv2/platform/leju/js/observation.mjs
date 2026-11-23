/** Read-only projections of kuavo_msgs/BatteryInfo. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u8", 1, 0], // battery_id
    ["u32", 1, 0], // voltage
    ["i32", 1, 0], // current
    ["u32", 1, 0], // remaining_capacity
    ["u32", 1, 0], // full_capacity
    ["u8", 1, 0], // percentage
    ["u16", 1, 0], // cycle_count
    ["u32", 1, 0], // protection_flags
    ["i16", 6, 0], // temperatures
    ["u32", 1, 0], // timestamp_sec
    ["u32", 1, 0], // timestamp_nsec
];

/** Read voltage from the complete record. Invalid data or an invalid index returns undefined. */
export function read_voltage(data) {
    return project(data, 0, fields, 1, 0);
}

/** Read current from the complete record. Invalid data or an invalid index returns undefined. */
export function read_current(data) {
    return project(data, 0, fields, 2, 0);
}

/** Read percentage from the complete record. Invalid data or an invalid index returns undefined. */
export function read_percentage(data) {
    return project(data, 0, fields, 5, 0);
}

/** Read temperatures from the complete record. Invalid data or an invalid index returns undefined. */
export function read_temperatures(data, index) {
    return project(data, 0, fields, 8, index);
}
