//! Read-only projections of builtin_interfaces/Duration.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // sec
    Field(4, 1, 0), // nanosec
];

/// Read sec.
pub fn read_sec(data: &[u8]) -> Option<i32> {
    let bits = reader::project(data, 1, LAYOUT, 0, 0)?;
    Some(bits as i32)
}

/// Read nanosec.
pub fn read_nanosec(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 1, LAYOUT, 1, 0)?;
    Some(bits as u32)
}
