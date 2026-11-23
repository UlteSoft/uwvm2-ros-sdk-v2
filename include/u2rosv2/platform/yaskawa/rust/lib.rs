//! Read-only projections of motoros2_interfaces/ErrorInfo.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // number
    Field(0, 1, 0), // message
    Field(4, 1, 0), // sub_code
    Field(4, 1, 0), // datetime_sec
    Field(4, 1, 0), // datetime_nanosec
];

/// Read number.
pub fn read_number(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 1, LAYOUT, 0, 0)?;
    Some(bits as u32)
}

/// Read sub_code.
pub fn read_sub_code(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 1, LAYOUT, 2, 0)?;
    Some(bits as i32)
}

/// Read datetime_sec.
pub fn read_datetime_sec(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 1, LAYOUT, 3, 0)?;
    Some(bits as i32)
}

/// Read datetime_nanosec.
pub fn read_datetime_nanosec(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 1, LAYOUT, 4, 0)?;
    Some(bits as u32)
}
