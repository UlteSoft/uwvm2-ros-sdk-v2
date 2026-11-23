//! Read-only projections of dsr_msgs/LogAlarm.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // level
    Field(4, 1, 0), // group
    Field(4, 1, 0), // index
    Field(0, 3, 0), // param
];

/// Read level.
pub fn read_level(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(bits as i32)
}

/// Read group.
pub fn read_group(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 0, LAYOUT, 1, 0)?;
    Some(bits as i32)
}

/// Read index.
pub fn read_index(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 0, LAYOUT, 2, 0)?;
    Some(bits as i32)
}
