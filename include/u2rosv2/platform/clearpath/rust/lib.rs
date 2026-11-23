//! Read-only projections of clearpath_dock_msgs/DockState.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

pub const UNDOCKED: i32 = 0;
pub const DOCKED: i32 = 1;
pub const IN_PROGRESS: i32 = 2;
pub const FAILED: i32 = 3;
pub const CANCELLED: i32 = 4;
const LAYOUT: &[Field] = &[
    Field(1, 1, 0), // state
];

/// Read state.
pub fn read_state(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(bits as u8)
}
