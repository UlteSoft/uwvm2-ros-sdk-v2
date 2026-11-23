//! Read-only projections of franka_msgs/Elbow.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

pub mod cdr;

const LAYOUT: &[Field] = &[
    Field(8, 2, 0), // position
    Field(8, 2, 0), // desired_position
    Field(8, 2, 0), // commanded_position
    Field(8, 2, 0), // commanded_velocity
    Field(8, 2, 0), // commanded_acceleration
];

/// Read position at a zero-based index.
pub fn read_position(data: &[u8], index: usize) -> Option<f64> {
    let bits = reader::project(data, 1, LAYOUT, 0, index)?;
    Some(f64::from_bits(bits))
}

/// Read desired_position at a zero-based index.
pub fn read_desired_position(data: &[u8], index: usize) -> Option<f64> {
    let bits = reader::project(data, 1, LAYOUT, 1, index)?;
    Some(f64::from_bits(bits))
}

/// Read commanded_position at a zero-based index.
pub fn read_commanded_position(data: &[u8], index: usize) -> Option<f64> {
    let bits = reader::project(data, 1, LAYOUT, 2, index)?;
    Some(f64::from_bits(bits))
}

/// Read commanded_velocity at a zero-based index.
pub fn read_commanded_velocity(data: &[u8], index: usize) -> Option<f64> {
    let bits = reader::project(data, 1, LAYOUT, 3, index)?;
    Some(f64::from_bits(bits))
}

/// Read commanded_acceleration at a zero-based index.
pub fn read_commanded_acceleration(data: &[u8], index: usize) -> Option<f64> {
    let bits = reader::project(data, 1, LAYOUT, 4, index)?;
    Some(f64::from_bits(bits))
}
