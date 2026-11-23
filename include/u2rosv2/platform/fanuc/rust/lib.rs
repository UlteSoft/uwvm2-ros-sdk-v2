//! Read-only projections of fanuc_msgs/ForceSensor.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // force_x
    Field(4, 1, 0), // force_y
    Field(4, 1, 0), // force_z
    Field(4, 1, 0), // moment_x
    Field(4, 1, 0), // moment_y
    Field(4, 1, 0), // moment_z
    Field(4, 1, 0), // fs_type
];

/// Read force_x.
pub fn read_force_x(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 0, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read force_z.
pub fn read_force_z(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 2, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read moment_z.
pub fn read_moment_z(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 5, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read fs_type.
pub fn read_fs_type(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 1, LAYOUT, 6, 0)?;
    Some(bits as u32)
}
