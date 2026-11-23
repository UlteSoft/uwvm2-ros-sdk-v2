//! Read-only projections of geometry_msgs/Quaternion.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(8, 1, 0), // x
    Field(8, 1, 0), // y
    Field(8, 1, 0), // z
    Field(8, 1, 0), // w
];

/// Read x.
pub fn read_x(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 3, LAYOUT, 0, 0)?;
    Some(f64::from_bits(bits))
}

/// Read y.
pub fn read_y(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 3, LAYOUT, 1, 0)?;
    Some(f64::from_bits(bits))
}

/// Read z.
pub fn read_z(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 3, LAYOUT, 2, 0)?;
    Some(f64::from_bits(bits))
}

/// Read w.
pub fn read_w(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 3, LAYOUT, 3, 0)?;
    Some(f64::from_bits(bits))
}
