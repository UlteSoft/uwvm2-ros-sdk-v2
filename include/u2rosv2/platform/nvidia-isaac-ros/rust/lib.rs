//! Read-only projections of isaac_ros_tensor_list_interfaces/TensorShape.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(1, 1, 0), // rank
    Field(4, 0, 0), // dims
];

/// Read rank.
pub fn read_rank(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 1, LAYOUT, 0, 0)?;
    Some(bits as u8)
}

/// Read dims at a zero-based index.
pub fn read_dims(data: &[u8], index: usize) -> Option<u32> {
    let bits = reader::project(data, 1, LAYOUT, 1, index)?;
    Some(bits as u32)
}
