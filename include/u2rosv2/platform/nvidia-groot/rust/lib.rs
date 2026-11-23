//! Read-only projections of DROID observation.state.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 9, 0), // eef_9d
    Field(4, 1, 0), // gripper_position
    Field(4, 7, 0), // joint_position
];

/// Read eef_9d at a zero-based index.
pub fn read_eef_9d(data: &[u8], index: usize) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 0, index)?;
    Some(f32::from_bits(bits as u32))
}

/// Read gripper_position.
pub fn read_gripper_position(data: &[u8]) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 1, 0)?;
    Some(f32::from_bits(bits as u32))
}

/// Read joint_position at a zero-based index.
pub fn read_joint_position(data: &[u8], index: usize) -> Option<f32> {
    let bits = reader::project(data, 0, LAYOUT, 2, index)?;
    Some(f32::from_bits(bits as u32))
}
