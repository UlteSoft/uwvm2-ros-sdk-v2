/** Read-only projections of kuka_driver_interfaces/KssStatus. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u8", 1, 0], // control_mode
    ["u8", 1, 0], // cycle_time
    ["bool", 1, 1], // drives_powered
    ["bool", 1, 1], // emergency_stop
    ["bool", 1, 1], // guard_stop
    ["bool", 1, 1], // in_motion
    ["bool", 1, 1], // motion_possible
    ["u8", 1, 0], // operation_mode
    ["bool", 1, 1], // robot_stopped
];

export const UNSPECIFIED = 0;
export const JOINT_POSITION_CONTROL = 1;
export const CARTESIAN_POSITION_CONTROL = 5;
export const RSI_4MS = 1;
export const RSI_12MS = 2;
export const T1 = 1;
export const T2 = 2;
export const AUT = 3;
export const EXT = 4;
/** Read cycle_time from the complete record. Invalid data or an invalid index returns undefined. */
export function read_cycle_time(data) {
    return project(data, 1, fields, 1, 0);
}

/** Read drives_powered from the complete record. Invalid data or an invalid index returns undefined. */
export function read_drives_powered(data) {
    return project(data, 1, fields, 2, 0);
}

/** Read guard_stop from the complete record. Invalid data or an invalid index returns undefined. */
export function read_guard_stop(data) {
    return project(data, 1, fields, 4, 0);
}

/** Read operation_mode from the complete record. Invalid data or an invalid index returns undefined. */
export function read_operation_mode(data) {
    return project(data, 1, fields, 7, 0);
}
