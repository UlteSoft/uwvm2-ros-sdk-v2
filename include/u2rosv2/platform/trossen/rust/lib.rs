//! Read-only projections of interbotix_xs_msgs/JointTemps.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(0, 0, 0), // names
    Field(4, 0, 0), // temps
];

/// Read temps at a zero-based index.
pub fn read_temps(data: &[u8], index: usize) -> Option<i32> {
    let bits = reader::project(data, 0, LAYOUT, 1, index)?;
    Some(bits as i32)
}
