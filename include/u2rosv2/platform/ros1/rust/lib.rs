//! Read-only projections of std_msgs/Time.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // data_sec
    Field(4, 1, 0), // data_nsec
];

/// Read data_sec.
pub fn read_data_sec(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(bits as u32)
}

/// Read data_nsec.
pub fn read_data_nsec(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 0, LAYOUT, 1, 0)?;
    Some(bits as u32)
}
