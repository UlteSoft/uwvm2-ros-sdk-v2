/** Read-only projections of ur_dashboard_msgs/SafetyStatus over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

export const NORMAL: i32 = 1;
export const REDUCED: i32 = 2;
export const PROTECTIVE_STOP: i32 = 3;
export const RECOVERY: i32 = 4;
export const SAFEGUARD_STOP: i32 = 5;
export const SYSTEM_EMERGENCY_STOP: i32 = 6;
export const ROBOT_EMERGENCY_STOP: i32 = 7;
export const VIOLATION: i32 = 8;
export const FAULT: i32 = 9;
export const VALIDATE_JOINT_ID: i32 = 10;
export const UNDEFINED_SAFETY_MODE: i32 = 11;
export const AUTOMATIC_MODE_SAFEGUARD_STOP: i32 = 12;
export const SYSTEM_THREE_POSITION_ENABLING_STOP: i32 = 13;
export const TP_THREE_POSITION_ENABLING_STOP: i32 = 14;
export const IMMI_EMERGENCY_STOP: i32 = 15;
export const IMMI_SAFEGUARD_STOP: i32 = 16;
export const PROFISAFE_WAITING_FOR_PARAMETERS: i32 = 17;
export const PROFISAFE_AUTOMATIC_MODE_SAFEGUARD_STOP: i32 = 18;
export const PROFISAFE_SAFEGUARD_STOP: i32 = 19;
export const PROFISAFE_EMERGENCY_STOP: i32 = 20;
export const SAFETY_API_SAFEGUARD_STOP: i32 = 22;
export const IO_PLANE_STOP: i32 = 23;
function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(1, size, fromReply)) return false;
    if (!field(1, 1, 0, wanted == 0, index)) return false; // status
    return finish();
}

/** Last successfully decoded status. */
export let status: i8 = 0;

/** Validate the complete request or reply span, then publish status. */
export function read_status(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    status = <i8>bits;
    return true;
}
