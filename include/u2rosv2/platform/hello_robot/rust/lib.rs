//! Read-only projections of Wacc_Protocol_P0.unpack_status.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // ax
    Field(4, 1, 0), // ay
    Field(4, 1, 0), // az
    Field(2, 1, 0), // a0
    Field(1, 1, 0), // d0
    Field(1, 1, 0), // d1
    Field(1, 1, 0), // d2
    Field(1, 1, 0), // d3
    Field(4, 1, 0), // single_tap_count
    Field(4, 1, 0), // state
    Field(4, 1, 0), // timestamp
    Field(4, 1, 0), // debug
];

/// Read ax.
pub fn read_ax(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read az.
pub fn read_az(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 2, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read a0.
pub fn read_a0(data: &[u8]) -> Option<i16> {
    let bits = reader::project(data, 0, LAYOUT, 3, 0)?;
    Some(bits as i16)
}

/// Read single_tap_count.
pub fn read_single_tap_count(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 0, LAYOUT, 8, 0)?;
    Some(bits as u32)
}

/// Read timestamp.
pub fn read_timestamp(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 0, LAYOUT, 10, 0)?;
    Some(bits as u32)
}
