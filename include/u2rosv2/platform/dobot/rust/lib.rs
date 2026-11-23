//! Read-only projections of dobot_msgs_v4/RobotStatus.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(1, 1, 1), // is_enable
    Field(1, 1, 1), // is_connected
];

/// Read is_enable.
pub fn read_is_enable(data: &[u8]) -> Option<bool> {
    let bits = reader::project(data, 1, LAYOUT, 0, 0)?;
    Some(bits != 0)
}

/// Read is_connected.
pub fn read_is_connected(data: &[u8]) -> Option<bool> {
    let bits = reader::project(data, 1, LAYOUT, 1, 0)?;
    Some(bits != 0)
}
