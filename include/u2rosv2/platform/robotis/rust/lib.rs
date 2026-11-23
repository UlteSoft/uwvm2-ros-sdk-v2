//! Read-only projections of turtlebot3_msgs/SensorState.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

pub const BUMPER_FORWARD: i32 = 1;
pub const BUMPER_BACKWARD: i32 = 2;
pub const CLIFF: i32 = 1;
pub const SONAR: i32 = 1;
pub const ILLUMINATION: i32 = 1;
pub const BUTTON0: i32 = 1;
pub const BUTTON1: i32 = 2;
pub const ERROR_LEFT_MOTOR: i32 = 1;
pub const ERROR_RIGHT_MOTOR: i32 = 2;
pub const TORQUE_ON: i32 = 1;
pub const TORQUE_OFF: i32 = 2;
const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // header_seq
    Field(4, 1, 0), // header_stamp_sec
    Field(4, 1, 0), // header_stamp_nsec
    Field(0, 1, 0), // header_frame_id
    Field(1, 1, 0), // bumper
    Field(4, 1, 0), // cliff
    Field(4, 1, 0), // sonar
    Field(4, 1, 0), // illumination
    Field(1, 1, 0), // led
    Field(1, 1, 0), // button
    Field(1, 1, 1), // torque
    Field(4, 1, 0), // left_encoder
    Field(4, 1, 0), // right_encoder
    Field(4, 1, 0), // battery
];

/// Read bumper.
pub fn read_bumper(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 0, LAYOUT, 4, 0)?;
    Some(bits as u8)
}

/// Read left_encoder.
pub fn read_left_encoder(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 0, LAYOUT, 11, 0)?;
    Some(bits as i32)
}

/// Read right_encoder.
pub fn read_right_encoder(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 0, LAYOUT, 12, 0)?;
    Some(bits as i32)
}

/// Read battery.
pub fn read_battery(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 13, 0)?;
    Some(f32::from_bits(bits as u32))
}
