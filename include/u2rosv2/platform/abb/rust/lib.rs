//! Read-only projections of abb_rapid_msgs/Pos.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

pub mod ros1;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // x
    Field(4, 1, 0), // y
    Field(4, 1, 0), // z
];

/// Read x.
pub fn read_x(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read y.
pub fn read_y(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 1, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read z.
pub fn read_z(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 2, 0)?;
    Some(f32::from_bits(bits as u32))
}
