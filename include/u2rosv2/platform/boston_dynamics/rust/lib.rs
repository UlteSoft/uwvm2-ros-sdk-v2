//! Read-only projections of bosdyn.api.PointCloud.data.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, -4, 0), // xyz
];

/// Read xyz at a zero-based index.
pub fn read_x(data: &[u8], index: usize) -> Option<f32> {
    let index = index.checked_mul(3)?.checked_add(0)?;
    let bits = reader::project(data, 0, LAYOUT, 0, index)?;
    Some(f32::from_bits(bits as u32))
}

/// Read xyz at a zero-based index.
pub fn read_y(data: &[u8], index: usize) -> Option<f32> {
    let index = index.checked_mul(3)?.checked_add(1)?;
    let bits = reader::project(data, 0, LAYOUT, 0, index)?;
    Some(f32::from_bits(bits as u32))
}

/// Read xyz at a zero-based index.
pub fn read_z(data: &[u8], index: usize) -> Option<f32> {
    let index = index.checked_mul(3)?.checked_add(2)?;
    let bits = reader::project(data, 0, LAYOUT, 0, index)?;
    Some(f32::from_bits(bits as u32))
}
