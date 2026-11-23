//! Read-only projections of xarm_msgs/IOState.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // digital_1
    Field(4, 1, 0), // digital_2
    Field(4, 1, 0), // analog_1
    Field(4, 1, 0), // analog_2
];

/// Read digital_1.
pub fn read_digital_1(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(bits as i32)
}

/// Read digital_2.
pub fn read_digital_2(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 0, LAYOUT, 1, 0)?;
    Some(bits as i32)
}

/// Read analog_1.
pub fn read_analog_1(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 2, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read analog_2.
pub fn read_analog_2(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 3, 0)?;
    Some(f32::from_bits(bits as u32))
}
