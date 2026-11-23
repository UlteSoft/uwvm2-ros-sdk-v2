/** Read-only projections of scout_msgs/ScoutBmsStatus. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["f64", 1, 0], // soc
    ["f64", 1, 0], // soh
    ["f64", 1, 0], // battery_voltage
    ["f64", 1, 0], // battery_current
    ["f64", 1, 0], // battery_temperature
    ["u8", 1, 0], // alarm_status_1
    ["u8", 1, 0], // alarm_status_2
    ["u8", 1, 0], // warning_status_1
    ["u8", 1, 0], // warning_status_2
];

/** Read soc from the complete record. Invalid data or an invalid index returns undefined. */
export function read_soc(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read battery_voltage from the complete record. Invalid data or an invalid index returns undefined. */
export function read_battery_voltage(data) {
    return project(data, 0, fields, 2, 0);
}

/** Read battery_current from the complete record. Invalid data or an invalid index returns undefined. */
export function read_battery_current(data) {
    return project(data, 0, fields, 3, 0);
}

/** Read alarm_status_1 from the complete record. Invalid data or an invalid index returns undefined. */
export function read_alarm_status_1(data) {
    return project(data, 0, fields, 5, 0);
}
