//! Read-only projections of flexiv_msgs/Digital.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(1, 1, 0), // pin
    Field(1, 1, 1), // state
];

/// Read pin.
pub fn read_pin(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 1, LAYOUT, 0, 0)?;
    Some(bits as u8)
}

/// Read state.
pub fn read_state(data: &[u8]) -> Option<bool> {
    let bits = reader::project(data, 1, LAYOUT, 1, 0)?;
    Some(bits != 0)
}
