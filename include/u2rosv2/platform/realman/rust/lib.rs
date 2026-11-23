//! Read-only projections of rm_ros_interfaces/Jointerrorcode.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(2, 0, 0), // joint_error
    Field(1, 1, 0), // dof
];

/// Read joint_error at a zero-based index.
pub fn read_joint_error(data: &[u8], index: usize) -> Option<u16> {
    let bits = reader::project(data, 1, LAYOUT, 0, index)?;
    Some(bits as u16)
}

/// Read dof.
pub fn read_dof(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 1, LAYOUT, 1, 0)?;
    Some(bits as u8)
}
