//! Read-only projections of simulator_pub_msg.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(8, 1, 0), // timestamp
    Field(4, 1, 2), // motor_num
    Field(8, -1, 0), // q
    Field(8, -1, 0), // q_dot
    Field(8, 3, 0), // acc
    Field(8, 3, 0), // omega
    Field(8, 4, 0), // quat
    Field(8, 1, 0), // lf_touch
    Field(8, 1, 0), // rf_touch
    Field(8, 3, 0), // pos
    Field(8, 3, 0), // vel
];

/// Read timestamp.
pub fn read_timestamp(data: &[u8]) -> Option<i64> {
    let bits = reader::project(data, 2, LAYOUT, 0, 0)?;
    Some(bits as i64)
}

/// Read q at a zero-based index.
pub fn read_q(data: &[u8], index: usize) -> Option<f64> {
    let bits = reader::project(data, 2, LAYOUT, 2, index)?;
    Some(f64::from_bits(bits))
}

/// Read q_dot at a zero-based index.
pub fn read_q_dot(data: &[u8], index: usize) -> Option<f64> {
    let bits = reader::project(data, 2, LAYOUT, 3, index)?;
    Some(f64::from_bits(bits))
}

/// Read lf_touch.
pub fn read_lf_touch(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 2, LAYOUT, 7, 0)?;
    Some(f64::from_bits(bits))
}

/// Read rf_touch.
pub fn read_rf_touch(data: &[u8]) -> Option<f64> {
    let bits = reader::project(data, 2, LAYOUT, 8, 0)?;
    Some(f64::from_bits(bits))
}
