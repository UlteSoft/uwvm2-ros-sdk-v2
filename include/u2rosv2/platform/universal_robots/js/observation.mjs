/** Read-only projections of ur_dashboard_msgs/SafetyStatus. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["i8", 1, 0], // status
];

export const NORMAL = 1;
export const REDUCED = 2;
export const PROTECTIVE_STOP = 3;
export const RECOVERY = 4;
export const SAFEGUARD_STOP = 5;
export const SYSTEM_EMERGENCY_STOP = 6;
export const ROBOT_EMERGENCY_STOP = 7;
export const VIOLATION = 8;
export const FAULT = 9;
export const VALIDATE_JOINT_ID = 10;
export const UNDEFINED_SAFETY_MODE = 11;
export const AUTOMATIC_MODE_SAFEGUARD_STOP = 12;
export const SYSTEM_THREE_POSITION_ENABLING_STOP = 13;
export const TP_THREE_POSITION_ENABLING_STOP = 14;
export const IMMI_EMERGENCY_STOP = 15;
export const IMMI_SAFEGUARD_STOP = 16;
export const PROFISAFE_WAITING_FOR_PARAMETERS = 17;
export const PROFISAFE_AUTOMATIC_MODE_SAFEGUARD_STOP = 18;
export const PROFISAFE_SAFEGUARD_STOP = 19;
export const PROFISAFE_EMERGENCY_STOP = 20;
export const SAFETY_API_SAFEGUARD_STOP = 22;
export const IO_PLANE_STOP = 23;
/** Read status from the complete record. Invalid data or an invalid index returns undefined. */
export function read_status(data) {
    return project(data, 1, fields, 0, 0);
}
