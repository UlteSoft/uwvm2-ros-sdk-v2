//! Read-only projections of aimdk_msgs/JointState.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(0, 1, 0), // name
    Field(8, 1, 0), // position
    Field(8, 1, 0), // velocity
    Field(8, 1, 0), // effort
    Field(2, 1, 0), // error_code
];

/// Read position.
pub fn read_position(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 1, LAYOUT, 1, 0)?;
    Some(f64::from_bits(bits))
}

/// Read velocity.
pub fn read_velocity(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 1, LAYOUT, 2, 0)?;
    Some(f64::from_bits(bits))
}

/// Read effort.
pub fn read_effort(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 1, LAYOUT, 3, 0)?;
    Some(f64::from_bits(bits))
}

/// Read error_code.
pub fn read_error_code(data: &[u8]) -> Option<u16> {
    let bits = reader::project(data, 1, LAYOUT, 4, 0)?;
    Some(bits as u16)
}
