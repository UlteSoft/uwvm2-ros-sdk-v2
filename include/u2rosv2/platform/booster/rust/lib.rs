//! Read-only projections of booster_interface/ImuState.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 3, 0), // rpy
    Field(4, 3, 0), // gyro
    Field(4, 3, 0), // acc
];

/// Read rpy at a zero-based index.
pub fn read_rpy(data: &[u8], index: usize) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 0, index)?;
    Some(f32::from_bits(bits as u32))
}

/// Read gyro at a zero-based index.
pub fn read_gyro(data: &[u8], index: usize) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 1, index)?;
    Some(f32::from_bits(bits as u32))
}

/// Read acc at a zero-based index.
pub fn read_acc(data: &[u8], index: usize) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 2, index)?;
    Some(f32::from_bits(bits as u32))
}
