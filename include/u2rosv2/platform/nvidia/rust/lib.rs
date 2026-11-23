//! Read-only projections of isaac_ros_nova_interfaces/EncoderTicks.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(4, 1, 0), // header_stamp_sec
    Field(4, 1, 0), // header_stamp_nanosec
    Field(0, 1, 0), // header_frame_id
    Field(4, 1, 0), // left_ticks
    Field(4, 1, 0), // right_ticks
    Field(8, 1, 0), // encoder_timestamp
];

/// Read left_ticks.
pub fn read_left_ticks(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 1, LAYOUT, 3, 0)?;
    Some(bits as u32)
}

/// Read right_ticks.
pub fn read_right_ticks(data: &[u8]) -> Option<u32> {
    let bits = reader::project(data, 1, LAYOUT, 4, 0)?;
    Some(bits as u32)
}

/// Read encoder_timestamp.
pub fn read_encoder_timestamp(data: &[u8]) -> Option<u64> {
    let bits = reader::project(data, 1, LAYOUT, 5, 0)?;
    Some(bits)
}
