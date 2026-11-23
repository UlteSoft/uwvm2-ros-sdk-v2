//! Read-only projections of drdds/ImuDataValue.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // roll
    Field(4, 1, 0), // pitch
    Field(4, 1, 0), // yaw
    Field(4, 1, 0), // omega_x
    Field(4, 1, 0), // omega_y
    Field(4, 1, 0), // omega_z
    Field(4, 1, 0), // acc_x
    Field(4, 1, 0), // acc_y
    Field(4, 1, 0), // acc_z
];

/// Read roll.
pub fn read_roll(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 0, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read yaw.
pub fn read_yaw(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 2, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read omega_z.
pub fn read_omega_z(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 5, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read acc_z.
pub fn read_acc_z(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 1, LAYOUT, 8, 0)?;
    Some(f32::from_bits(bits as u32))
}
