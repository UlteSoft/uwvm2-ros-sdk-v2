//! Read-only projections of myarm_communication/MyArmPumpStatus.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(1, 1, 1), // status
    Field(1, 1, 0), // pin1
    Field(1, 1, 0), // pin2
];

/// Read status.
pub fn read_status(data: &[u8]) -> Option<bool> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(bits != 0)
}

/// Read pin1.
pub fn read_pin1(data: &[u8]) -> Option<i8> {
    let bits = reader::project(data, 0, LAYOUT, 1, 0)?;
    Some(bits as i8)
}

/// Read pin2.
pub fn read_pin2(data: &[u8]) -> Option<i8> {
    let bits = reader::project(data, 0, LAYOUT, 2, 0)?;
    Some(bits as i8)
}
