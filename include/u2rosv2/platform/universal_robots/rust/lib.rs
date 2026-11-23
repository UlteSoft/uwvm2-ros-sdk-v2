//! Read-only projections of ur_dashboard_msgs/SafetyStatus.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

pub mod cdr;

pub const NORMAL: i32 = 1;
pub const REDUCED: i32 = 2;
pub const PROTECTIVE_STOP: i32 = 3;
pub const RECOVERY: i32 = 4;
pub const SAFEGUARD_STOP: i32 = 5;
pub const SYSTEM_EMERGENCY_STOP: i32 = 6;
pub const ROBOT_EMERGENCY_STOP: i32 = 7;
pub const VIOLATION: i32 = 8;
pub const FAULT: i32 = 9;
pub const VALIDATE_JOINT_ID: i32 = 10;
pub const UNDEFINED_SAFETY_MODE: i32 = 11;
pub const AUTOMATIC_MODE_SAFEGUARD_STOP: i32 = 12;
pub const SYSTEM_THREE_POSITION_ENABLING_STOP: i32 = 13;
pub const TP_THREE_POSITION_ENABLING_STOP: i32 = 14;
pub const IMMI_EMERGENCY_STOP: i32 = 15;
pub const IMMI_SAFEGUARD_STOP: i32 = 16;
pub const PROFISAFE_WAITING_FOR_PARAMETERS: i32 = 17;
pub const PROFISAFE_AUTOMATIC_MODE_SAFEGUARD_STOP: i32 = 18;
pub const PROFISAFE_SAFEGUARD_STOP: i32 = 19;
pub const PROFISAFE_EMERGENCY_STOP: i32 = 20;
pub const SAFETY_API_SAFEGUARD_STOP: i32 = 22;
pub const IO_PLANE_STOP: i32 = 23;
const LAYOUT: &[Field] = &[
    Field(1, 1, 0), // status
];

/// Read status.
pub fn read_status(data: &[u8]) -> Option<i8> {
    let bits = reader::project(data, 1, LAYOUT, 0, 0)?;
    Some(bits as i8)
}
