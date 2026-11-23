//! Read-only projections of kuka_driver_interfaces/KssStatus.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

pub const UNSPECIFIED: i32 = 0;
pub const JOINT_POSITION_CONTROL: i32 = 1;
pub const CARTESIAN_POSITION_CONTROL: i32 = 5;
pub const RSI_4MS: i32 = 1;
pub const RSI_12MS: i32 = 2;
pub const T1: i32 = 1;
pub const T2: i32 = 2;
pub const AUT: i32 = 3;
pub const EXT: i32 = 4;
const LAYOUT: &[Field] = &[
    Field(1, 1, 0), // control_mode
    Field(1, 1, 0), // cycle_time
    Field(1, 1, 1), // drives_powered
    Field(1, 1, 1), // emergency_stop
    Field(1, 1, 1), // guard_stop
    Field(1, 1, 1), // in_motion
    Field(1, 1, 1), // motion_possible
    Field(1, 1, 0), // operation_mode
    Field(1, 1, 1), // robot_stopped
];

/// Read cycle_time.
pub fn read_cycle_time(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 1, LAYOUT, 1, 0)?;
    Some(bits as u8)
}

/// Read drives_powered.
pub fn read_drives_powered(data: &[u8]) -> Option<bool> {
    let bits = reader::project(data, 1, LAYOUT, 2, 0)?;
    Some(bits != 0)
}

/// Read guard_stop.
pub fn read_guard_stop(data: &[u8]) -> Option<bool> {
    let bits = reader::project(data, 1, LAYOUT, 4, 0)?;
    Some(bits != 0)
}

/// Read operation_mode.
pub fn read_operation_mode(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 1, LAYOUT, 7, 0)?;
    Some(bits as u8)
}
